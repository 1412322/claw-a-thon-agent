from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.database.vector_db import (
    ingest_file, get_project_documents,
    get_all_projects, delete_file_chunks
)
from app.database.version_store import (
    save_version, update_chunks_count,
    get_versions, get_all_versioned_docs,
    get_latest_version_number
)
from app.services.diff_service import analyze_diff, extract_text_from_bytes
from app.schemas import (
    UploadResponse, ProjectInfo,
    VersionInfo, VersionedDoc, DiffRequest, DiffResponse
)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "md", "txt"}
PROJECT_REGISTRY: dict[str, str] = {}


# ─────────────────────────────────────────
# UPLOAD
# ─────────────────────────────────────────

@router.post("/upload-doc", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    project_name: str = Form(...),
):
    ext = file.filename.lower().split(".")[-1] if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File '.{ext}' không hỗ trợ. Chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File quá lớn (tối đa 20MB)")

    PROJECT_REGISTRY[project_id] = project_name

    # 1. Extract text để lưu version
    raw_text = extract_text_from_bytes(contents, file.filename)

    # 2. Lưu version — tự động tăng version number
    version_info = save_version(project_id, file.filename, raw_text)

    if version_info["is_duplicate"]:
        return UploadResponse(
            status="success",
            message=f"File '{file.filename}' không có thay đổi — vẫn dùng version {version_info['version']}",
            chunks_added=0,
            project_id=project_id,
            version=version_info["version"],
            is_new_version=False
        )

    # 3. Xóa chunks cũ của file này trước khi ingest version mới
    delete_file_chunks(project_id, file.filename)

    # 4. Ingest version mới vào ChromaDB
    chunks_added = ingest_file(
        file_bytes=contents,
        filename=file.filename,
        project_id=project_id
    )

    # 5. Cập nhật chunk count vào version store
    update_chunks_count(project_id, file.filename, chunks_added)

    version_num = version_info["version"]
    is_new = version_num > 1

    return UploadResponse(
        status="success",
        message=(
            f"Cập nhật lên version {version_num} thành công!"
            if is_new else
            f"Version 1 đã được nạp cho '{file.filename}'"
        ),
        chunks_added=chunks_added,
        project_id=project_id,
        version=version_num,
        is_new_version=is_new
    )


# ─────────────────────────────────────────
# VERSION HISTORY
# ─────────────────────────────────────────

@router.get("/{project_id}/versions", response_model=list[VersionedDoc])
async def list_versioned_docs(project_id: str):
    """Lấy danh sách tất cả files có versioning của 1 project."""
    return get_all_versioned_docs(project_id)


@router.get("/{project_id}/versions/{filename:path}", response_model=list[VersionInfo])
async def get_file_versions(project_id: str, filename: str):
    """Lấy toàn bộ lịch sử version của 1 file."""
    versions = get_versions(project_id, filename)
    if not versions:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy version nào cho file '{filename}'")
    return versions


# ─────────────────────────────────────────
# COMPARE / DIFF
# ─────────────────────────────────────────

@router.post("/{project_id}/compare", response_model=DiffResponse)
async def compare_versions(project_id: str, body: DiffRequest):
    """
    So sánh 2 version của 1 file trong project.
    Qwen sẽ phân tích thay đổi và ảnh hưởng đến QC/Dev.
    """
    latest = get_latest_version_number(project_id, body.filename)
    if latest == 0:
        raise HTTPException(status_code=404, detail=f"File '{body.filename}' chưa có version nào.")

    if body.version_a == body.version_b:
        raise HTTPException(status_code=400, detail="Phải chọn 2 version khác nhau để so sánh.")

    if body.version_a > latest or body.version_b > latest:
        raise HTTPException(
            status_code=400,
            detail=f"Version không hợp lệ. File này có tối đa version {latest}."
        )

    try:
        result = await analyze_diff(
            project_id=project_id,
            filename=body.filename,
            version_a=body.version_a,
            version_b=body.version_b
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích: {str(e)}")


# ─────────────────────────────────────────
# PROJECT LIST
# ─────────────────────────────────────────

@router.get("/", response_model=list[ProjectInfo])
async def list_projects():
    project_ids = get_all_projects()
    result = []

    for pid in project_ids:
        docs = get_project_documents(pid)
        result.append(ProjectInfo(
            project_id=pid,
            project_name=PROJECT_REGISTRY.get(pid, pid),
            documents=docs,
            total_chunks=sum(d["chunks"] for d in docs)
        ))

    for pid, pname in PROJECT_REGISTRY.items():
        if pid not in project_ids:
            result.append(ProjectInfo(
                project_id=pid,
                project_name=pname,
                documents=[],
                total_chunks=0
            ))

    return result


@router.get("/{project_id}", response_model=ProjectInfo)
async def get_project(project_id: str):
    docs = get_project_documents(project_id)
    return ProjectInfo(
        project_id=project_id,
        project_name=PROJECT_REGISTRY.get(project_id, project_id),
        documents=docs,
        total_chunks=sum(d["chunks"] for d in docs)
    )
