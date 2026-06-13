import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_core.documents import Document
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

import tempfile, os
from app.config import get_settings

settings = get_settings()
COLLECTION_NAME = "agent_knowledge"

# Global embedding instance (cached)
_embedding_instance = None

def get_huggingface_embeddings():
    """Get HuggingFace embedding model (free, no API key needed)."""
    global _embedding_instance
    if _embedding_instance is None:
        # Use sentence-transformers model (free, works offline after first download)
        _embedding_instance = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    return _embedding_instance

class HuggingFaceEmbeddingFunction(EmbeddingFunction):
    """
    ChromaDB-compatible embedding function using HuggingFace sentence-transformers.
    Free, no API key required.
    """
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = get_huggingface_embeddings()
        return embeddings.embed_documents(input)

def _get_ef():
    return HuggingFaceEmbeddingFunction()

def _get_client():
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)

def _get_collection():
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_get_ef()
    )


def ingest_file(file_bytes: bytes, filename: str, project_id: str) -> int:
    ext = filename.lower().split(".")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if ext == "pdf":
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
        elif ext in ("docx", "doc"):
            loader = Docx2txtLoader(tmp_path)
            docs = loader.load()
        else:
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            docs = [Document(page_content=text)]

        print(f"[VectorDB] Loaded {len(docs)} documents from {filename}")
        for i, doc in enumerate(docs):
            print(f"[VectorDB] Doc {i}: {len(doc.page_content)} chars")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=150,
            separators=["\n\n", "\n", ".", " "]
        )
        chunks = splitter.split_documents(docs)

        print(f"[VectorDB] Split into {len(chunks)} chunks")

        if not chunks:
            print(f"[VectorDB] No chunks created!")
            return 0

        collection = _get_collection()

        # Build data for chromadb
        ids, documents, metadatas = [], [], []
        for i, chunk in enumerate(chunks):
            ids.append(f"{project_id}_{filename}_{i}")
            documents.append(chunk.page_content)
            metadatas.append({
                "project_id": project_id,
                "source_file": filename,
            })

        # Upsert in batches of 50
        batch = 50
        for start in range(0, len(ids), batch):
            print(f"[VectorDB] Upserting batch {start//batch + 1}: {len(ids[start:start+batch])} items")
            collection.upsert(
                ids=ids[start:start+batch],
                documents=documents[start:start+batch],
                metadatas=metadatas[start:start+batch],
            )
            print(f"[VectorDB] Batch {start//batch + 1} completed")

        print(f"[VectorDB] Total chunks added: {len(chunks)}")
        return len(chunks)
    finally:
        os.unlink(tmp_path)


def retrieve_context(query: str, project_id: str, k: int = 3) -> str:
    """
    Retrieve context from vector DB.
    Default k=3 (reduced from 5) for faster response.
    """
    try:
        collection = _get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=min(k, collection.count()),
            where={"project_id": project_id},
            include=["documents"]  # Only include documents, skip metadatas for speed
        )

        docs = results.get("documents", [[]])[0]

        if not docs:
            return ""

        # Simple concatenation for speed
        return "\n\n".join(docs)
    except Exception as e:
        print(f"[RAG] retrieve error: {e}")
        return ""


def get_project_documents(project_id: str) -> list[dict]:
    try:
        collection = _get_collection()
        results = collection.get(
            where={"project_id": project_id},
            include=["metadatas"]
        )
        file_chunks: dict[str, int] = {}
        for meta in results["metadatas"]:
            fname = meta.get("source_file", "unknown")
            file_chunks[fname] = file_chunks.get(fname, 0) + 1
        return [{"filename": f, "source": f, "chunks": c} for f, c in file_chunks.items()]
    except Exception:
        return []


def get_all_projects() -> list[str]:
    try:
        collection = _get_collection()
        results = collection.get(include=["metadatas"])
        ids = {m.get("project_id") for m in results["metadatas"] if m.get("project_id")}
        return sorted(ids)
    except Exception:
        return []

def delete_file_chunks(project_id: str, filename: str):
    """Xóa toàn bộ chunks của 1 file trong 1 project trước khi ingest version mới."""
    try:
        collection = _get_collection()
        results = collection.get(
            where={"$and": [{"project_id": project_id}, {"source_file": filename}]},
            include=[]
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"[VectorDB] Deleted {len(ids_to_delete)} old chunks for {filename} in {project_id}")
    except Exception as e:
        print(f"[VectorDB] delete_file_chunks error: {e}")
