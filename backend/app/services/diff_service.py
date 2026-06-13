from openai import AsyncOpenAI
from app.config import get_settings
from app.database.version_store import get_version_content, get_versions

settings = get_settings()

DIFF_PROMPT_TEMPLATE = """Bạn là chuyên gia phân tích thay đổi tài liệu đặc tả phần mềm.
So sánh 2 version của tài liệu "{filename}" và phân tích tác động.

---
## VERSION {v_old} (CŨ)
{content_old}

---
## VERSION {v_new} (MỚI)
{content_new}

---
Hãy phân tích và trả về ĐÚNG định dạng sau, không thêm bớt:

## 📋 Tóm tắt
[1-2 câu mô tả tổng quan thay đổi]

## ➕ Thêm mới
[Liệt kê từng requirement/rule mới được thêm vào. Nếu không có, ghi "Không có thay đổi."]

## ✏️ Cập nhật
[Liệt kê từng thay đổi theo format: **Tên mục**: ~~Giá trị cũ~~ → Giá trị mới. Nếu không có, ghi "Không có thay đổi."]

## ❌ Xóa bỏ
[Liệt kê từng requirement/rule bị xóa. Nếu không có, ghi "Không có thay đổi."]

## 🧪 Ảnh hưởng đến QC
[Liệt kê cụ thể:
- Test case nào cần THÊM MỚI
- Test case nào cần CẬP NHẬT
- Test case nào có thể BỎ]

## 💻 Ảnh hưởng đến Dev
[Liệt kê cụ thể:
- API/endpoint nào thay đổi
- Business logic/validation nào cần sửa
- Config/constant nào cần cập nhật]"""


async def analyze_diff(
    project_id: str,
    filename: str,
    version_a: int,
    version_b: int
) -> dict:
    """
    Compare 2 versions of a document using Greenode (VNG Cloud).
    Returns structured diff analysis.
    """
    content_a = get_version_content(project_id, filename, version_a)
    content_b = get_version_content(project_id, filename, version_b)

    if content_a is None:
        raise ValueError(f"Version {version_a} không tồn tại cho file '{filename}'")
    if content_b is None:
        raise ValueError(f"Version {version_b} không tồn tại cho file '{filename}'")

    # Ensure version_a is always the older one
    old_ver, new_ver = (version_a, version_b) if version_a < version_b else (version_b, version_a)
    old_content, new_content = (content_a, content_b) if version_a < version_b else (content_b, content_a)

    prompt = DIFF_PROMPT_TEMPLATE.format(
        filename=filename,
        v_old=old_ver,
        v_new=new_ver,
        content_old=old_content,
        content_new=new_content,
    )

    client = AsyncOpenAI(
        api_key=settings.greenode_api_key,
        base_url="https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1"
    )

    response = await client.chat.completions.create(
        model=settings.greenode_model,
        messages=[
            {"role": "system", "content": "Bạn là chuyên gia phân tích tài liệu phần mềm. Hãy trả lời bằng tiếng Việt, định dạng Markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=3000
    )

    return {
        "project_id": project_id,
        "filename": filename,
        "version_old": old_ver,
        "version_new": new_ver,
        "analysis": response.choices[0].message.content,
    }


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from uploaded file for version storage.
    Reuses loader logic from vector_db but returns raw string.
    """
    import tempfile, os
    from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
    from langchain_core.documents import Document

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
                return f.read()

        return "\n\n".join(d.page_content for d in docs)
    finally:
        os.unlink(tmp_path)
