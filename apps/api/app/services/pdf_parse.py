"""
读 PDF 文字：能抽出字的走电子件；几乎没字的当扫描件，尝试 OCR。
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader

SCAN_TEXT_THRESHOLD = 80


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
    if len(compact) >= SCAN_TEXT_THRESHOLD:
        return ParsedPdf(text=text.strip(), source="electronic")

    ocr_text, ocr_error = _ocr_pdf(data)
    if ocr_text and len("".join(ocr_text.split())) > len(compact):
        return ParsedPdf(text=ocr_text.strip(), source="scanned", error=ocr_error)
    if compact:
        return ParsedPdf(text=text.strip(), source="scanned", error=ocr_error)
    return ParsedPdf(text="", source="scanned", error=ocr_error or "未读到文字，请手工填写要素")


def _ocr_pdf(data: bytes) -> tuple[str, str | None]:
    try:
        import pypdfium2 as pdfium
        import pytesseract
    except ImportError:
        return "", "环境未安装 OCR 组件，扫描件请手工核对"

    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        return "", "未安装 Tesseract，扫描件请手工核对"

    try:
        document = pdfium.PdfDocument(data)
    except Exception as exc:  # noqa: BLE001
        return "", f"扫描件渲染失败：{exc}"

    chunks: list[str] = []
    langs = "chi_sim+eng"
    for index in range(min(len(document), 4)):
        page = document[index]
        bitmap = page.render(scale=2)
        image = bitmap.to_pil()
        try:
            chunks.append(pytesseract.image_to_string(image, lang=langs))
        except pytesseract.TesseractError:
            chunks.append(pytesseract.image_to_string(image, lang="eng"))
    return "\n".join(chunks), None
