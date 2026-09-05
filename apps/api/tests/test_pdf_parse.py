from io import BytesIO

from PIL import Image

from app.core.config import get_settings
from app.services.extract import extract_fields, has_enough_draft_fields
from app.services.pdf_parse import parse_pdf_bytes
from app.services.qwen_ocr import MAX_IMAGE_SIDE, jpeg_for_ocr, qwen_ocr_image


class _Page:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _Reader:
    def __init__(self, pages: list[_Page]) -> None:
        self.pages = pages


COVER = (
    "合同编号：HT-SCAN-1\n"
    "甲方：星河科技有限公司\n"
    "乙方：本地运营主体\n"
    "合同总金额（元）：120000.00"
)


def _enable_qwen(monkeypatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "sk-test")
    get_settings.cache_clear()


def _blank_pdf(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.pdf_parse.PdfReader",
        lambda *_args, **_kwargs: _Reader([_Page("")]),
    )


def test_electronic_pdf_skips_ocr(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.pdf_parse.PdfReader",
        lambda *_args, **_kwargs: _Reader([_Page("甲方：星河科技有限公司合同正文内容" * 8)]),
    )

    def boom(*_args, **_kwargs):
        raise AssertionError("电子件不应走 OCR")

    monkeypatch.setattr("app.services.pdf_parse._ocr_pdf", boom)
    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.source == "electronic"
    assert "星河" in result.text


def test_scanned_pdf_uses_qwen_one_page(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _blank_pdf(monkeypatch)
    monkeypatch.setattr(
        "app.services.pdf_parse.iter_pdf_jpegs",
        lambda _data, **_kwargs: iter([b"page-1"]),
    )
    monkeypatch.setattr(
        "app.services.pdf_parse.qwen_ocr_image",
        lambda _image: (COVER, None),
    )
    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.source == "scanned"
    assert "HT-SCAN-1" in result.text
    assert result.error is None


def test_scanned_pdf_stops_when_cover_has_enough_fields(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _blank_pdf(monkeypatch)
    rendered: list[bytes] = []

    def fake_pages(_data: bytes, **_kwargs):
        rendered.append(b"page-1")
        yield b"page-1"
        rendered.append(b"page-2")
        yield b"page-2"

    calls: list[bytes] = []

    def fake_ocr(image: bytes) -> tuple[str, str | None]:
        calls.append(image)
        if image == b"page-1":
            return COVER, None
        raise AssertionError("封面字段已齐，不应再识别后面的页")

    monkeypatch.setattr("app.services.pdf_parse.iter_pdf_jpegs", fake_pages)
    monkeypatch.setattr("app.services.pdf_parse.qwen_ocr_image", fake_ocr)

    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.source == "scanned"
    assert "HT-SCAN-1" in result.text
    assert calls == [b"page-1"]
    assert rendered == [b"page-1"]


def test_scanned_pdf_reads_next_page_when_cover_missing_number(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _blank_pdf(monkeypatch)
    pages = {
        b"page-1": "甲方：星河科技有限公司\n乙方：本地运营主体\n合同总金额（元）：100",
        b"page-2": "合同编号：HT-PAGE-2",
        b"page-3": "这一页不该被识别",
    }
    calls: list[bytes] = []

    def fake_ocr(image: bytes) -> tuple[str, str | None]:
        calls.append(image)
        return pages[image], None

    monkeypatch.setattr(
        "app.services.pdf_parse.iter_pdf_jpegs",
        lambda _data, **_kwargs: iter([b"page-1", b"page-2", b"page-3"]),
    )
    monkeypatch.setattr("app.services.pdf_parse.qwen_ocr_image", fake_ocr)

    result = parse_pdf_bytes(b"%PDF-fake")
    assert calls == [b"page-1", b"page-2"]
    assert "HT-PAGE-2" in result.text
    assert "不该被识别" not in result.text


def test_qwen_failure_does_not_fallback(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _blank_pdf(monkeypatch)
    monkeypatch.setattr(
        "app.services.pdf_parse.iter_pdf_jpegs",
        lambda _data, **_kwargs: iter([b"page-1"]),
    )
    monkeypatch.setattr(
        "app.services.pdf_parse.qwen_ocr_image",
        lambda _image: ("", "Qwen OCR 请求失败：timeout"),
    )
    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.source == "scanned"
    assert result.text == ""
    assert result.error and "Qwen OCR 请求失败" in result.error


def test_scanned_pdf_without_qwen_key_does_not_ocr(monkeypatch) -> None:
    _blank_pdf(monkeypatch)
    called = {"render": False, "qwen": False}

    def fake_pages(_data: bytes, **_kwargs):
        called["render"] = True
        yield b"page-1"

    def fake_ocr(_image: bytes) -> tuple[str, str | None]:
        called["qwen"] = True
        return "", "不该调用"

    monkeypatch.setattr("app.services.pdf_parse.iter_pdf_jpegs", fake_pages)
    monkeypatch.setattr("app.services.pdf_parse.qwen_ocr_image", fake_ocr)

    result = parse_pdf_bytes(b"%PDF-fake")
    assert called == {"render": False, "qwen": False}
    assert result.source == "scanned"
    assert result.text == ""
    assert result.error and "QWEN_API_KEY" in result.error


def test_short_electronic_text_with_fields_skips_ocr(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.pdf_parse.PdfReader",
        lambda *_args, **_kwargs: _Reader([_Page(COVER)]),
    )

    def boom(*_args, **_kwargs):
        raise AssertionError("草稿要素已齐，不应再走 OCR")

    monkeypatch.setattr("app.services.pdf_parse._ocr_pdf", boom)
    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.source == "electronic"
    assert "HT-SCAN-1" in result.text


def test_qwen_request_is_single_page_and_disables_thinking(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": "合同编号：HT-SCAN-1"}}]}

    def fake_post(url: str, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr("app.services.qwen_ocr.httpx.post", fake_post)
    text, error = qwen_ocr_image(b"abc")
    assert error is None
    assert text == "合同编号：HT-SCAN-1"
    payload = captured["json"]
    assert payload["model"] == "qwen3.5-ocr"
    assert payload["max_tokens"] == 400
    assert "enable_thinking" not in payload
    assert captured["url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    content = payload["messages"][0]["content"]
    images = [item for item in content if item.get("type") == "image_url"]
    assert len(images) == 1
    assert images[0]["max_pixels"] == 32 * 32 * 1280
    prompt = next(item["text"] for item in content if item.get("type") == "text")
    assert "全部可见文字" not in prompt
    assert "合同编号" in prompt
    monkeypatch.setenv("QWEN_API_KEY", "")
    get_settings.cache_clear()


def test_general_vl_model_turns_off_thinking(monkeypatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "sk-test")
    monkeypatch.setenv("QWEN_OCR_MODEL", "qwen3.7-plus")
    get_settings.cache_clear()
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": "甲方：甲"}}]}

    def fake_post(_url: str, **kwargs):
        captured["json"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr("app.services.qwen_ocr.httpx.post", fake_post)
    qwen_ocr_image(b"abc")
    assert captured["json"]["enable_thinking"] is False
    assert captured["json"]["model"] == "qwen3.7-plus"
    monkeypatch.setenv("QWEN_OCR_MODEL", "qwen3.5-ocr")
    get_settings.cache_clear()


def test_jpeg_for_ocr_caps_long_edge() -> None:
    image = Image.new("RGB", (2000, 2800), "white")
    jpeg = jpeg_for_ocr(image)
    out = Image.open(BytesIO(jpeg))
    assert max(out.size) <= MAX_IMAGE_SIDE


def test_qwen_skipped_without_key() -> None:
    text, error = qwen_ocr_image(b"abc")
    assert text == ""
    assert error and "QWEN_API_KEY" in error


def test_has_enough_draft_fields() -> None:
    assert has_enough_draft_fields(extract_fields(COVER)) is True
    assert (
        has_enough_draft_fields(
            extract_fields("甲方：星河科技有限公司\n乙方：本地运营主体\n合同总金额（元）：100")
        )
        is False
    )
    assert (
        has_enough_draft_fields(extract_fields("发票代码：012001900104\n发票号码：12345678")) is True
    )
