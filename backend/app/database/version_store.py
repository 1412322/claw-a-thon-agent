import json
import os
import hashlib
from datetime import datetime

VERSION_FILE = "./chroma_db/doc_versions.json"


def _load() -> dict:
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data: dict):
    os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _key(project_id: str, filename: str) -> str:
    return f"{project_id}::{filename}"


def save_version(project_id: str, filename: str, content: str) -> dict:
    """
    Lưu version mới cho file.
    Trả về: { version, changed, is_duplicate }
    """
    data = _load()
    k = _key(project_id, filename)

    if k not in data:
        data[k] = []

    content_hash = hashlib.md5(content.encode()).hexdigest()

    # Không lưu nếu content giống hệt version trước
    if data[k] and data[k][-1]["hash"] == content_hash:
        latest = data[k][-1]
        return {
            "version": latest["version"],
            "changed": False,
            "is_duplicate": True
        }

    version_num = len(data[k]) + 1
    entry = {
        "version": version_num,
        "filename": filename,
        "project_id": project_id,
        "hash": content_hash,
        "content": content,
        "uploaded_at": datetime.now().isoformat(),
        "chunks_count": 0
    }

    data[k].append(entry)
    _save(data)

    return {
        "version": version_num,
        "changed": True,
        "is_duplicate": False
    }


def update_chunks_count(project_id: str, filename: str, chunks_count: int):
    """Cập nhật số chunks sau khi ingest xong."""
    data = _load()
    k = _key(project_id, filename)
    if k in data and data[k]:
        data[k][-1]["chunks_count"] = chunks_count
        _save(data)


def get_versions(project_id: str, filename: str) -> list:
    """Lấy toàn bộ lịch sử version của 1 file."""
    data = _load()
    k = _key(project_id, filename)
    versions = data.get(k, [])
    # Trả về list bỏ field content (nặng) để hiển thị
    return [
        {
            "version": v["version"],
            "filename": v["filename"],
            "uploaded_at": v["uploaded_at"],
            "chunks_count": v["chunks_count"],
            "hash": v["hash"][:8],  # Short hash để display
        }
        for v in versions
    ]


def get_version_content(project_id: str, filename: str, version: int) -> str | None:
    """Lấy nội dung text của 1 version cụ thể."""
    data = _load()
    k = _key(project_id, filename)
    for v in data.get(k, []):
        if v["version"] == version:
            return v["content"]
    return None


def get_latest_version_number(project_id: str, filename: str) -> int:
    """Lấy version number mới nhất."""
    data = _load()
    k = _key(project_id, filename)
    versions = data.get(k, [])
    return versions[-1]["version"] if versions else 0


def get_all_versioned_docs(project_id: str) -> list:
    """Lấy tất cả files có versioning của 1 project."""
    data = _load()
    result = []
    for k, versions in data.items():
        pid, fname = k.split("::", 1)
        if pid == project_id and versions:
            latest = versions[-1]
            result.append({
                "filename": fname,
                "total_versions": len(versions),
                "latest_version": latest["version"],
                "latest_uploaded_at": latest["uploaded_at"],
                "chunks_count": latest["chunks_count"],
            })
    return result
