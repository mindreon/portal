"""
扫描件走 Qwen 视觉模型认字。电子 PDF 不会调用这里。

用百炼 OpenAI 兼容接口：每次只发一页 JPEG，只要纯文本。
思考模式默认开着会又慢又容易编造编号，OCR 必须关掉。
"""

from __future__ import annotations

import base64
from collections.abc import Iterator
from io import BytesIO

import httpx

from app.core.config import get_settings

OCR_PROMPT = (
    "请提取这一页合同扫描件上的全部可见文字，按阅读顺序输出纯文本。"
    "不要翻译、不要总结、不要编造合同编号或金额。"
    "看不清的字段留空。不要使用 Markdown。"
)
MAX_PAGES = 4
SOFT_EMPTY = "Qwen OCR 没有读到文字"


class PdfRenderError(Exception):
    """PDF 页渲染失败。扫描件 OCR 开始前就会遇到。"""


def qwen_ocr_image(image_jpeg: bytes) -> tuple[str, str | None]:
    """识别单页扫描图。没配 key 时返回明确错误，不回退其它引擎。"""
    settings = get_settings()
    if not settings.qwen_ocr_enabled:
        return "", "未配置 QWEN_API_KEY，扫描件无法自动识别，请手工填写。"
    if not image_jpeg:
        return "", "扫描件没有可识别的页面"

    encoded = base64.b64encode(image_jpeg).decode("ascii")
    content = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
        {"type": "text", "text": OCR_PROMPT},
    ]

    url = settings.qwen_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.qwen_ocr_model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "enable_thinking": False,
    }
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
            bitmap = document[index].render(scale=2)
            image = bitmap.to_pil().convert("RGB")
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=75)
            yield buffer.getvalue()
    finally:
        close = getattr(document, "close", None)
        if callable(close):
            close()


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
