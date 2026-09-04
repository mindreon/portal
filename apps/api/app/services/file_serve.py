"""原件下载 / 在线预览共用的响应头。"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi.responses import FileResponse

IMAGE_SUFFIXES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}


def media_type_for(name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    return IMAGE_SUFFIXES.get(suffix, "application/octet-stream")


def original_file_response(path: str, original_name: str, *, inline: bool) -> FileResponse:
    disposition = "inline" if inline else "attachment"
    encoded = quote(original_name)
    ascii_name = original_name.encode("ascii", "replace").decode("ascii") or "file"
    return FileResponse(
        path,
        media_type=media_type_for(original_name),
        filename=original_name,
        content_disposition_type=disposition,
        headers={
            "Content-Disposition": f"{disposition}; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=120",
        },
    )
