"""
读 PDF 文字。能本地抽字就绝不调用模型。

流程（越往下越贵）：
1. 内容哈希相同 → 整份跳过（imports 里做，0 token）
2. pypdf 抽电子字（0 token）
3. 抽到的字已经够填草稿 → 当电子件，不上 OCR
4. 字很少 → 当扫描件，按页 OCR；封面要素齐了就停
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader

from app.core.config import get_settings
from app.services.extract import extract_fields, has_enough_draft_fields
from app.services.qwen_ocr import (
    MAX_PAGES,
    SOFT_EMPTY,
    PdfRenderError,
    iter_pdf_jpegs,
    qwen_ocr_image,
)

SCAN_TEXT_THRESHOLD = 80

logger = logging.getLogger(__name__)


@dataclass
class ParsedPdf:
    text: str
    source: str  # electronic | scanned
    error: str | None = None


def parse_pdf_bytes(data: bytes) -> ParsedPdf:
    text = ""
    try:
        reader = PdfReader(BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:  # noqa: BLE001 — 坏文件也要让批次继续
        return ParsedPdf(text="", source="scanned", error=f"无法打开 PDF：{exc}")

    compact = "".join(text.split())
    # 字少但要素已齐：多见于封面可提取、正文是图的混合件，不必再花 OCR。
    if compact and has_enough_draft_fields(extract_fields(text)):
        return ParsedPdf(text=text.strip(), source="electronic")
    if len(compact) >= SCAN_TEXT_THRESHOLD:
        return ParsedPdf(text=text.strip(), source="electronic")

    ocr_text, ocr_error = _ocr_pdf(data)
    if ocr_text and len("".join(ocr_text.split())) > len(compact):
        return ParsedPdf(text=ocr_text.strip(), source="scanned", error=ocr_error)
    if compact:
        return ParsedPdf(text=text.strip(), source="scanned", error=ocr_error)
    return ParsedPdf(text="", source="scanned", error=ocr_error or "未读到文字，请手工填写要素")


def _ocr_pdf(data: bytes) -> tuple[str, str | None]:
    """扫描件按页走 OCR。失败不回退到其它引擎。"""
    if not get_settings().qwen_ocr_enabled:
        return "", "未配置 QWEN_API_KEY，扫描件无法自动识别，请手工填写。"

    chunks: list[str] = []
    last_error: str | None = None
    try:
        for page_no, jpeg in enumerate(iter_pdf_jpegs(data, max_pages=MAX_PAGES), start=1):
            page_text, page_error = qwen_ocr_image(jpeg)
            if page_text:
                chunks.append(page_text)
                if has_enough_draft_fields(extract_fields("\n".join(chunks))):
                    logger.info("扫描件 OCR 在第 %s 页后停止：草稿字段已齐", page_no)
                    break
                continue
            if page_error in (None, SOFT_EMPTY):
                last_error = page_error or SOFT_EMPTY
                continue
            last_error = page_error
            if not chunks:
                return "", page_error
            logger.warning("扫描件第 %s 页 OCR 失败，保留已识别文字：%s", page_no, page_error)
            break
    except PdfRenderError as exc:
        return "\n".join(chunks), (None if chunks else str(exc))

    if not chunks:
        return "", last_error or "扫描件 OCR 未读到文字，请手工填写要素"
    return "\n".join(chunks), last_error
