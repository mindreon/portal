"""原件下载 / 在线预览共用的响应头。"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import FileResponse, Response

IMAGE_SUFFIXES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}

# 附件按内容 hash 去重，落盘后不会改。只让浏览器私有缓存，不要让 Nginx 公共缓存。
CACHE_CONTROL = "private, max-age=86400"


def media_type_for(name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    return IMAGE_SUFFIXES.get(suffix, "application/octet-stream")


def _quoted_etag(content_hash: str | None) -> str | None:
    if not content_hash:
        return None
    return f'"{content_hash}"'


def _if_none_match_hits(request: Request | None, etag: str | None) -> bool:
    """浏览器带 If-None-Match 且和文件 hash 一致时，可以只回 304，不必再传整份 PDF。"""
    if request is None or not etag:
        return False
    incoming = request.headers.get("if-none-match")
    if not incoming:
        return False
    needle = etag.strip('"')
    for tag in incoming.split(","):
        cleaned = tag.strip().removeprefix("W/").strip().strip('"')
        if cleaned == needle or cleaned == "*":
            return True
    return False


def original_file_response(
    path: str,
    original_name: str,
    *,
    inline: bool,
    content_hash: str | None = None,
    request: Request | None = None,
) -> FileResponse | Response:
    disposition = "inline" if inline else "attachment"
    encoded = quote(original_name)
    ascii_name = original_name.encode("ascii", "replace").decode("ascii") or "file"
    etag = _quoted_etag(content_hash)
    headers = {
        "Content-Disposition": f"{disposition}; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": CACHE_CONTROL,
        # 生产最外层是 Nginx。这个头让它不要把整份 PDF 先攒进磁盘再发给浏览器。
        "X-Accel-Buffering": "no",
    }
    if etag:
        headers["ETag"] = etag
    if _if_none_match_hits(request, etag) and request is not None and request.headers.get("range") is None:
        return Response(status_code=304, headers=headers)
    return FileResponse(
        path,
        media_type=media_type_for(original_name),
        filename=original_name,
        content_disposition_type=disposition,
        headers=headers,
    )
