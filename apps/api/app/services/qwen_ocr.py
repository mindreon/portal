"""
用通义千问理解每一页合同/发票。

统一默认模型 qwen3.7-plus（可用 QWEN_OCR_MODEL 覆盖）。
有电子字就只发该页文本；扫描页才发缩小后的 JPEG。
思考模式会编造编号，抽取时必须关掉。
"""

from __future__ import annotations

import base64
import json
import logging
import re
from collections.abc import Iterator
from io import BytesIO

import httpx
from PIL import Image

from app.core.config import get_settings
from app.services.extract import (
    ExtractedFields,
    already_as_prompt_dict,
    fields_from_llm_payload,
    still_needed_from_payload,
)

logger = logging.getLogger(__name__)

# 合同默认至少读 5 页（不够就全读）；信息不齐再继续，最多 12 页，避免整本附录。
MIN_PAGES = 5
MAX_PAGES = 12
# 长边 1280：扫描件上印刷字仍可读，图像 token 比 scale=2 原图少一半。
MAX_IMAGE_SIDE = 1280
JPEG_QUALITY = 70
MAX_OUTPUT_TOKENS = 1000
MAX_PAGE_CHARS = 8000
# 百炼 OCR 模型会按 max_pixels 再缩一次；通用 3.7 不走这个参数。
MAX_PIXELS = 32 * 32 * 1280
MIN_PIXELS = 32 * 32 * 4
SOFT_EMPTY = "本页没有读到可用信息"

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I)


class PdfRenderError(Exception):
    """PDF 页渲染失败。扫描件开始理解前就会遇到。"""


def jpeg_for_ocr(image: Image.Image) -> bytes:
    """扫描页缩到够用的分辨率，少传像素就是少花图像 token。"""
    rgb = image.convert("RGB")
    width, height = rgb.size
    long_edge = max(width, height)
    if long_edge > MAX_IMAGE_SIDE:
        ratio = MAX_IMAGE_SIDE / long_edge
        rgb = rgb.resize((max(1, int(width * ratio)), max(1, int(height * ratio))))
    buffer = BytesIO()
    rgb.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buffer.getvalue()


def understand_page(
    *,
    already: ExtractedFields,
    page_text: str | None = None,
    image_jpeg: bytes | None = None,
) -> tuple[ExtractedFields, list[str], str | None]:
    """
    理解一页：返回本页抽到的字段、整份文件还缺什么、错误信息。
    没配 key 时返回明确错误，不回退到正则或其它引擎。
    """
    settings = get_settings()
    if not settings.qwen_ocr_enabled:
        return ExtractedFields(), [], "未配置 QWEN_API_KEY，无法理解合同内容，请手工填写。"
    if not (page_text and page_text.strip()) and not image_jpeg:
        return ExtractedFields(), [], "这一页没有可理解的内容"

    prompt = _build_prompt(already)
    content: list[dict] = []
    if image_jpeg:
        encoded = base64.b64encode(image_jpeg).decode("ascii")
        image_part: dict = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
        }
        if _is_ocr_model(settings.qwen_ocr_model):
            image_part["min_pixels"] = MIN_PIXELS
            image_part["max_pixels"] = MAX_PIXELS
        content.append(image_part)
    user_text = prompt
    if page_text and page_text.strip():
        clipped = page_text.strip()
        if len(clipped) > MAX_PAGE_CHARS:
            clipped = clipped[:MAX_PAGE_CHARS] + "\n…（本页后文已截断）"
        user_text = prompt + "\n\n本页文本：\n" + clipped
    content.append({"type": "text", "text": user_text})

    base = settings.qwen_base_url.strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    url = base.rstrip("/") + "/chat/completions"
    payload: dict = {
        "model": settings.qwen_ocr_model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
        "max_tokens": MAX_OUTPUT_TOKENS,
    }
    # 通用多模态默认会思考，抽取必须关掉；专用 OCR 模型没有这个开关。
    if not _is_ocr_model(settings.qwen_ocr_model):
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
        return ExtractedFields(), [], f"通义千问请求失败：{exc}"
    except ValueError:
        return ExtractedFields(), [], "通义千问返回了无法解析的内容"

    text = _message_text(body)
    data = _parse_json_object(text)
    if data is None:
        if not text.strip():
            return ExtractedFields(), [], SOFT_EMPTY
        logger.warning("通义千问未返回 JSON：%s", text[:200])
        return ExtractedFields(), [], "通义千问未返回可解析的 JSON"
    return fields_from_llm_payload(data), still_needed_from_payload(data), None


def iter_pdf_jpegs(data: bytes, *, max_pages: int = MAX_PAGES) -> Iterator[bytes]:
    """逐页渲成 JPEG。调用方理解够字段后可以中途停下。"""
    renderer = PdfRenderer(data)
    try:
        count = renderer.page_count()
        for index in range(min(count, max_pages)):
            yield renderer.jpeg(index)
    finally:
        renderer.close()


class PdfRenderer:
    """需要看扫描页时才打开渲染器，电子页只走文本。"""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._document = None

    def _open(self):
        if self._document is not None:
            return self._document
        try:
            import pypdfium2 as pdfium
        except ImportError as exc:
            raise PdfRenderError("环境未安装 PDF 渲染组件，扫描件请手工核对") from exc
        try:
            self._document = pdfium.PdfDocument(self._data)
        except Exception as exc:  # noqa: BLE001 — 坏扫描件也要让批次继续
            raise PdfRenderError(f"扫描件渲染失败：{exc}") from exc
        return self._document

    def page_count(self) -> int:
        return len(self._open())

    def jpeg(self, index: int) -> bytes:
        document = self._open()
        if index < 0 or index >= len(document):
            raise PdfRenderError(f"没有第 {index + 1} 页")
        # scale=1.5 ≈ 108dpi，再交给 jpeg_for_ocr 卡长边。
        bitmap = document[index].render(scale=1.5)
        return jpeg_for_ocr(bitmap.to_pil())

    def close(self) -> None:
        document = self._document
        self._document = None
        if document is None:
            return
        closer = getattr(document, "close", None)
        if callable(closer):
            closer()


def _build_prompt(already: ExtractedFields) -> str:
    already_json = json.dumps(already_as_prompt_dict(already), ensure_ascii=False)
    return (
        "你是合同/发票录入助手。请理解本页内容，抽取草稿要素，不要做条款摘要。\n"
        f"前面几页已经抽到：{already_json}\n"
        "规则：\n"
        "1. 只根据本页真实内容填写；本页没有或看不清的字段用空字符串或空数组，不要编造。\n"
        "2. 已有字段不要改成空；本页若有更完整的值可以填写。\n"
        "3. subject_name 只填合同正文中甲方采购或乙方销售的标的名称，优先抄「采购物」「合同标的」等明确条款；"
        "若明确条款列出多个独立采购物，按该条款原文列出；不要把多个配套项、功能模块、服务内容或附件清单拼成一串。\n"
        "4. subject_name 不要填公司名（例如北京时序天成技术有限公司），"
        "不要填合同标题（例如软件产品销售合同），"
        "不要填「软件产品」「产品及/或服务」这类空泛词，"
        "也不要从保密条款、附件功能清单、价格清单里抄配套项；若本页没有明确主标的，subject_name 留空。\n"
        "5. 付款分期只在本页写明期次名称和百分比时填写。\n"
        "6. still_needed 只列这份文件草稿还缺、而且从合同体例看应当存在的键。"
        "若还没读到具体采购物，把 subject_name 列入 still_needed。"
        "若合同里本来就没有分期或日期，不要列入 still_needed。\n"
        "7. 只输出一个 JSON 对象，不要 Markdown。\n"
        "JSON 形状：\n"
        '{"doc_type":"contract|invoice|unknown","contract_no":"","party_a":"","party_b":"",'
        '"subject_name":"","amount":"","signed_at":"","start_date":"","end_date":"","title":"",'
        '"invoices":[{"code":"","no":"","amount":""}],'
        '"schedules":[{"name":"","percent":0}],'
        '"still_needed":["party_a"]}'
    )


def _is_ocr_model(model: str) -> bool:
    return "ocr" in model.lower()


def _parse_json_object(text: str) -> dict | None:
    raw = _JSON_FENCE_RE.sub("", (text or "").strip()).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


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
