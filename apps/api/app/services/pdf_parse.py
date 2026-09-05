"""
读 PDF：一页一页交给通义千问理解，草稿信息齐了就停。

- 这一页能抽出电子字 → 只发文本给 3.7（比整页图便宜）
- 这一页几乎没字 → 渲成 JPEG 再理解
- 不在正文上做正则匹配
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from io import BytesIO

from pypdf import PdfReader

from app.core.config import get_settings
from app.services.extract import (
    ExtractedFields,
    extraction_complete,
    finalize_fields,
    is_usable_subject_name,
    merge_extracted_fields,
)
from app.services.qwen_ocr import MAX_PAGES, PdfRenderer, PdfRenderError, understand_page

# 一页压缩后少于此字数，当作扫描页看图。
PAGE_TEXT_MIN = 20

logger = logging.getLogger(__name__)


@dataclass
class ParsedPdf:
    text: str
    source: str  # electronic | scanned
    error: str | None = None
    fields: ExtractedFields = field(default_factory=ExtractedFields)


def parse_pdf_bytes(data: bytes) -> ParsedPdf:
    try:
        reader = PdfReader(BytesIO(data))
        page_texts = [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:  # noqa: BLE001 — 坏文件也要让批次继续
        return ParsedPdf(text="", source="scanned", error=f"无法打开 PDF：{exc}")

    if not page_texts:
        return ParsedPdf(text="", source="scanned", error="PDF 没有页面")

    if not get_settings().qwen_ocr_enabled:
        joined = "\n".join(text for text in page_texts if text.strip())
        compact = "".join(joined.split())
        source = "electronic" if len(compact) >= PAGE_TEXT_MIN else "scanned"
        return ParsedPdf(
            text=joined.strip(),
            source=source,
            error="未配置 QWEN_API_KEY，无法理解合同内容，请手工填写。",
        )

    return _understand_pdf(data, page_texts)


def _understand_pdf(data: bytes, page_texts: list[str]) -> ParsedPdf:
    merged = ExtractedFields()
    chunks: list[str] = []
    used_image = False
    last_error: str | None = None
    still_needed: list[str] | None = None
    renderer: PdfRenderer | None = None

    try:
        for index, page_text in enumerate(page_texts[:MAX_PAGES]):
            compact = "".join(page_text.split())
            image_jpeg: bytes | None = None
            send_text = page_text if len(compact) >= PAGE_TEXT_MIN else None
            if send_text is None:
                used_image = True
                if renderer is None:
                    renderer = PdfRenderer(data)
                try:
                    image_jpeg = renderer.jpeg(index)
                except PdfRenderError as exc:
                    last_error = str(exc)
                    if not chunks:
                        return ParsedPdf(text="", source="scanned", error=str(exc), fields=finalize_fields(merged))
                    logger.warning("第 %s 页渲染失败，保留已理解内容：%s", index + 1, exc)
                    break

            page_fields, page_needed, page_error = understand_page(
                already=merged,
                page_text=send_text,
                image_jpeg=image_jpeg,
            )
            if page_error:
                last_error = page_error
                if not chunks and _is_hard_error(page_error):
                    source = "scanned" if used_image else "electronic"
                    return ParsedPdf(text="", source=source, error=page_error, fields=finalize_fields(merged))
                logger.warning("第 %s 页理解失败：%s", index + 1, page_error)
                continue

            note = send_text.strip() if send_text else page_fields.title or f"（第 {index + 1} 页）"
            if note:
                chunks.append(note)
            merged, added = merge_extracted_fields(merged, page_fields)
            still_needed = page_needed
            if extraction_complete(merged, still_needed):
                logger.info("合同理解在第 %s 页后停止：草稿信息已齐", index + 1)
                break
            subject_ready = merged.doc_type == "invoice" or is_usable_subject_name(
                merged.subject_name,
                party_a=merged.party_a,
                party_b=merged.party_b,
                title=merged.title,
            )
            if not added and still_needed == [] and subject_ready:
                logger.info("合同理解在第 %s 页后停止：本页无新字段且模型认为已齐", index + 1)
                break
    finally:
        if renderer is not None:
            renderer.close()

    source = "scanned" if used_image else "electronic"
    text = "\n".join(chunks).strip()
    fields = finalize_fields(merged)
    if not text and last_error:
        return ParsedPdf(text="", source=source, error=last_error, fields=fields)
    return ParsedPdf(text=text, source=source, error=last_error, fields=fields)


def _is_hard_error(message: str) -> bool:
    return "请求失败" in message or "QWEN_API_KEY" in message or "无法解析" in message
