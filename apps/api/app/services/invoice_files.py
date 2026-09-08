"""发票 PDF 的落盘、校验和删除。和合同导入分开，避免互相踩目录。"""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

from app.core.config import get_settings

MAX_FILE_MB = 200
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024
UNSAFE_NAME = re.compile(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+")
PDF_MAGIC = b"%PDF"


def safe_name(name: str) -> str:
    base = Path(name.replace("\\", "/")).name
    cleaned = UNSAFE_NAME.sub("_", base).strip("._") or "invoice.pdf"
    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned}.pdf"
    return cleaned[:180]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_pdf(name: str, data: bytes) -> bool:
    """文件名和文件头都检查，避免有人把别的格式改后缀传上来。"""
    if not name.lower().endswith(".pdf"):
        return False
    return data.lstrip().startswith(PDF_MAGIC)


def write_invoice_pdf(invoice_id: int, original_name: str, data: bytes) -> Path:
    folder = Path(get_settings().upload_dir) / "invoices" / str(invoice_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex[:10]}_{safe_name(original_name)}"
    path.write_bytes(data)
    return path


def remove_stored_file(path: str | None) -> None:
    if not path:
        return
    stored = Path(path)
    stored.unlink(missing_ok=True)
    parent = stored.parent
    if parent.name.isdigit() and parent.parent.name == "invoices":
        try:
            parent.rmdir()
        except OSError:
            pass
