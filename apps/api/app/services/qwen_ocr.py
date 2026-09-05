"""
扫描件走百炼 OCR 认字。电子 PDF 不会调用这里。

Token 省法（精确优先）：
1. 用文档 OCR 模型，不要用通用多模态把整页正文读完。
2. 图先缩小再上传：图像 token ≈ 高×宽 / (32×32)。
3. 只要要素行，不要整页条款；输出上限压在几百 token。
4. 思考模式会编造编号，OCR 必须关掉。
"""

from __future__ import annotations

import base64
from collections.abc import Iterator
from io import BytesIO

import httpx
from PIL import Image

from app.core.config import get_settings

# 只抄草稿用得上的行。正则 extract_fields 认的就是这些标签。
OCR_PROMPT = (
    "只抄写本页能看清的合同或发票要素，按原文逐行输出，不要其它条款、签章、水印。"
    "标签尽量写成：合同编号、甲方、乙方、合同总金额（元）、合同签订时间、"
    "履约期限（起止）、发票代码、发票号码、发票金额（元）、第一期/尾款百分比。"
    "看不清的字段不要猜、不要编造。不要 Markdown。"
)
MAX_PAGES = 4
# 长边 1280：A4 上 10pt 字仍可读，图像 token 约为 scale=2 原图的一半。
MAX_IMAGE_SIDE = 1280
JPEG_QUALITY = 70
MAX_OUTPUT_TOKENS = 400
# 百炼 OCR 会按 max_pixels 再缩一次；与本地长边上限对齐。
MAX_PIXELS = 32 * 32 * 1280
MIN_PIXELS = 32 * 32 * 4
SOFT_EMPTY = "Qwen OCR 没有读到文字"


class PdfRenderError(Exception):
    """PDF 页渲染失败。扫描件 OCR 开始前就会遇到。"""


def jpeg_for_ocr(image: Image.Image) -> bytes:
    """缩到 OCR 够用的分辨率，少传像素就是少花图像 token。"""
    rgb = image.convert("RGB")
    width, height = rgb.size
    long_edge = max(width, height)
    if long_edge > MAX_IMAGE_SIDE:
        ratio = MAX_IMAGE_SIDE / long_edge
        rgb = rgb.resize((max(1, int(width * ratio)), max(1, int(height * ratio))))
    buffer = BytesIO()
    rgb.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buffer.getvalue()


def qwen_ocr_image(image_jpeg: bytes) -> tuple[str, str | None]:
    """识别单页扫描图。没配 key 时返回明确错误，不回退其它引擎。"""
    settings = get_settings()
    if not settings.qwen_ocr_enabled:
        return "", "未配置 QWEN_API_KEY，扫描件无法自动识别，请手工填写。"
    if not image_jpeg:
        return "", "扫描件没有可识别的页面"

    encoded = base64.b64encode(image_jpeg).decode("ascii")
    model = settings.qwen_ocr_model
    image_part: dict = {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
    }
    if _is_ocr_model(model):
        image_part["min_pixels"] = MIN_PIXELS
        image_part["max_pixels"] = MAX_PIXELS

    content = [
        image_part,
        {"type": "text", "text": OCR_PROMPT},
    ]

    base = settings.qwen_base_url.strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    url = base.rstrip("/") + "/chat/completions"
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "max_tokens": MAX_OUTPUT_TOKENS,
    }
    # 通用多模态默认会思考，OCR 必须关掉；专用 OCR 模型没有这个开关。
    if not _is_ocr_model(model):
        payload["enable_thinking"] = False
    try:
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.qwen_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90.0,
        )
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPError as exc:
        return "", f"Qwen OCR 请求失败：{exc}"
    except ValueError:
        return "", "Qwen OCR 返回了无法解析的内容"

    text = _message_text(body)
    if not text.strip():
        return "", SOFT_EMPTY
    return text.strip(), None


def iter_pdf_jpegs(data: bytes, *, max_pages: int = MAX_PAGES) -> Iterator[bytes]:
    """逐页渲成 JPEG。调用方识别够字段后可以中途停下，后面的页不会渲染。"""
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise PdfRenderError("环境未安装 PDF 渲染组件，扫描件请手工核对") from exc

    try:
        document = pdfium.PdfDocument(data)
    except Exception as exc:  # noqa: BLE001 — 坏扫描件也要让批次继续
        raise PdfRenderError(f"扫描件渲染失败：{exc}") from exc

    try:
        count = min(len(document), max_pages)
        for index in range(count):
            # scale=1.5 ≈ 108dpi，再交给 jpeg_for_ocr 卡长边。
            bitmap = document[index].render(scale=1.5)
            yield jpeg_for_ocr(bitmap.to_pil())
    finally:
        close = getattr(document, "close", None)
        if callable(close):
            close()


def _is_ocr_model(model: str) -> bool:
    return "ocr" in model.lower()


def _message_text(body: dict) -> str:
    choices = body.get("choices") or []
    if not choices:
        return ""
    content = (choices[0].get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return ""
