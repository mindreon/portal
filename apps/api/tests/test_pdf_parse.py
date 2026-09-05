from io import BytesIO

from PIL import Image

from app.core.config import get_settings
from app.services.extract import fields_from_llm_payload
from app.services.pdf_parse import parse_pdf_bytes
from app.services.qwen_ocr import MAX_IMAGE_SIDE, jpeg_for_ocr, understand_page


class _Page:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _Reader:
    def __init__(self, pages: list[_Page]) -> None:
        self.pages = pages


class _FakeRenderer:
    def __init__(self, _data: bytes) -> None:
        self.closed = False

    def jpeg(self, index: int) -> bytes:
        return [b"page-1", b"page-2", b"page-3"][index]

    def close(self) -> None:
        self.closed = True


def _enable_qwen(monkeypatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "sk-test")
    get_settings.cache_clear()


def _pages(monkeypatch, texts: list[str]) -> None:
    monkeypatch.setattr(
        "app.services.pdf_parse.PdfReader",
        lambda *_args, **_kwargs: _Reader([_Page(item) for item in texts]),
    )


def test_electronic_pages_understood_until_complete(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _pages(
        monkeypatch,
        [
            "第1页封面写了甲乙双方的正式名称，足够超过文本阈值。",
            "第2页写明合同编号金额以及签订日和履约起止期限。",
            "第3页是不该再理解的附录条款。",
        ],
    )
    calls: list[str | None] = []

    def fake_understand(*, already, page_text=None, image_jpeg=None):
        assert image_jpeg is None
        calls.append(page_text)
        if page_text and "第1页" in page_text:
            return (
                fields_from_llm_payload(
                    {"doc_type": "contract", "party_a": "星河科技有限公司", "party_b": "本地运营主体"}
                ),
                ["contract_no", "amount", "signed_at", "start_date", "end_date"],
                None,
            )
        if page_text and "第2页" in page_text:
            return (
                fields_from_llm_payload(
                    {
                        "doc_type": "contract",
                        "contract_no": "HT-1",
                        "amount": "120000",
                        "signed_at": "2026-01-01",
                        "start_date": "2026-01-01",
                        "end_date": "2026-12-31",
                        "subject_name": "AI 调度软件",
                    }
                ),
                [],
                None,
            )
        raise AssertionError("草稿已齐，不应再理解后面的页")

    monkeypatch.setattr("app.services.pdf_parse.understand_page", fake_understand)
    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.source == "electronic"
    assert result.fields.contract_no == "HT-1"
    assert result.fields.party_a == "星河科技有限公司"
    assert result.fields.amount is not None
    assert len(calls) == 2
    assert calls[1] and "第2页" in calls[1]


def test_generic_cover_subject_keeps_reading_for_goods_list(monkeypatch) -> None:
    """时序天成这类销售合同：封面常抽出公司名或「软件产品」，真正标的在后面清单页。"""
    _enable_qwen(monkeypatch)
    _pages(
        monkeypatch,
        [
            "第1页软件产品销售合同，甲方医院，乙方北京时序天成技术有限公司，金额已写明，内容足够长。",
            "第2页合同标的：AI调度软件、交换机、防火墙等设备，内容足够长。",
            "第3页附录保密条款。",
        ],
    )
    calls: list[str | None] = []

    def fake_understand(*, already, page_text=None, image_jpeg=None):
        calls.append(page_text)
        if page_text and "第1页" in page_text:
            return (
                fields_from_llm_payload(
                    {
                        "doc_type": "contract",
                        "contract_no": "HT-SXTC-1",
                        "party_a": "哈尔滨医科大学附属第一医院",
                        "party_b": "北京时序天成技术有限公司",
                        "amount": "100000",
                        "signed_at": "2026-01-01",
                        "start_date": "2026-01-01",
                        "end_date": "2026-12-31",
                        "subject_name": "北京时序天成技术有限公司",
                    }
                ),
                [],
                None,
            )
        if page_text and "第2页" in page_text:
            return (
                fields_from_llm_payload(
                    {"subject_name": "AI 调度软件、交换机、防火墙等设备"}
                ),
                [],
                None,
            )
        raise AssertionError("标的已齐，不应再读保密附录")

    monkeypatch.setattr("app.services.pdf_parse.understand_page", fake_understand)
    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.fields.subject_name == "AI 调度软件、交换机、防火墙等设备"
    assert result.fields.party_b == "北京时序天成技术有限公司"
    assert len(calls) == 2


def test_electronic_keeps_reading_for_payment_schedule(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _pages(
        monkeypatch,
        [
            "第1页已经有编号甲乙金额签订日和履约期限，内容足够长。",
            "第2页付款方式：第一期百分之三十，尾款百分之七十，内容足够长。",
            "第3页附录。",
        ],
    )
    calls: list[str | None] = []

    def fake_understand(*, already, page_text=None, image_jpeg=None):
        calls.append(page_text)
        if page_text and "第1页" in page_text:
            return (
                fields_from_llm_payload(
                    {
                        "doc_type": "contract",
                        "contract_no": "HT-PAY",
                        "party_a": "甲",
                        "party_b": "乙",
                        "amount": "100",
                        "signed_at": "2026-01-01",
                        "start_date": "2026-01-01",
                        "end_date": "2026-12-31",
                        "subject_name": "防火墙维保",
                    }
                ),
                ["schedules"],
                None,
            )
        if page_text and "第2页" in page_text:
            return (
                fields_from_llm_payload(
                    {"schedules": [{"name": "第一期", "percent": 30}, {"name": "尾款", "percent": 70}]}
                ),
                [],
                None,
            )
        raise AssertionError("分期已齐，不应再读附录")

    monkeypatch.setattr("app.services.pdf_parse.understand_page", fake_understand)
    result = parse_pdf_bytes(b"%PDF-fake")
    assert [item.name for item in result.fields.schedules] == ["第一期", "尾款"]
    assert len(calls) == 2


def test_scanned_pages_use_image_and_stop_when_complete(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _pages(monkeypatch, ["", "", ""])
    monkeypatch.setattr("app.services.pdf_parse.PdfRenderer", _FakeRenderer)
    calls: list[bytes | None] = []

    def fake_understand(*, already, page_text=None, image_jpeg=None):
        assert page_text is None
        calls.append(image_jpeg)
        if image_jpeg == b"page-1":
            return (
                fields_from_llm_payload(
                    {
                        "doc_type": "contract",
                        "contract_no": "HT-SCAN-1",
                        "party_a": "星河科技有限公司",
                        "party_b": "本地运营主体",
                        "amount": "120000.00",
                        "signed_at": "2026-01-01",
                        "start_date": "2026-01-01",
                        "end_date": "2026-12-31",
                        "subject_name": "AI 调度软件",
                    }
                ),
                [],
                None,
            )
        raise AssertionError("封面信息已齐，不应再看后面的扫描页")

    monkeypatch.setattr("app.services.pdf_parse.understand_page", fake_understand)
    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.source == "scanned"
    assert result.fields.contract_no == "HT-SCAN-1"
    assert calls == [b"page-1"]


def test_scanned_reads_next_page_when_number_still_needed(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _pages(monkeypatch, ["", "", ""])
    monkeypatch.setattr("app.services.pdf_parse.PdfRenderer", _FakeRenderer)
    calls: list[bytes | None] = []

    def fake_understand(*, already, page_text=None, image_jpeg=None):
        calls.append(image_jpeg)
        if image_jpeg == b"page-1":
            return (
                fields_from_llm_payload(
                    {"doc_type": "contract", "party_a": "星河科技有限公司", "party_b": "本地运营主体", "amount": "100"}
                ),
                ["contract_no"],
                None,
            )
        if image_jpeg == b"page-2":
            return fields_from_llm_payload({"contract_no": "HT-PAGE-2", "subject_name": "交换机"}), [], None
        raise AssertionError("编号已找到，不应再看第3页")

    monkeypatch.setattr("app.services.pdf_parse.understand_page", fake_understand)
    result = parse_pdf_bytes(b"%PDF-fake")
    assert calls == [b"page-1", b"page-2"]
    assert result.fields.contract_no == "HT-PAGE-2"


def test_qwen_failure_does_not_fallback(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    _pages(monkeypatch, [""])
    monkeypatch.setattr("app.services.pdf_parse.PdfRenderer", _FakeRenderer)
    monkeypatch.setattr(
        "app.services.pdf_parse.understand_page",
        lambda **_kwargs: (fields_from_llm_payload({}), [], "通义千问请求失败：timeout"),
    )
    result = parse_pdf_bytes(b"%PDF-fake")
    assert result.source == "scanned"
    assert result.text == ""
    assert result.error and "通义千问请求失败" in result.error


def test_without_key_does_not_call_model(monkeypatch) -> None:
    _pages(monkeypatch, ["甲方乙方以及足够长的电子正文，用来确认没有密钥时仍能留下文本。"])
    called = {"model": False}

    def boom(**_kwargs):
        called["model"] = True
        raise AssertionError("没配密钥时不应调用模型")

    monkeypatch.setattr("app.services.pdf_parse.understand_page", boom)
    result = parse_pdf_bytes(b"%PDF-fake")
    assert called == {"model": False}
    assert "甲方乙方" in result.text
    assert result.fields.party_a == ""
    assert result.error and "QWEN_API_KEY" in result.error


def test_understand_request_uses_37_and_disables_thinking(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"doc_type":"contract","contract_no":"HT-SCAN-1","still_needed":[]}'
                        }
                    }
                ]
            }

    def fake_post(url: str, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr("app.services.qwen_ocr.httpx.post", fake_post)
    fields, needed, error = understand_page(already=fields_from_llm_payload({}), page_text="合同编号 HT-SCAN-1")
    assert error is None
    assert fields.contract_no == "HT-SCAN-1"
    assert needed == []
    payload = captured["json"]
    assert payload["model"] == "qwen3.7-plus"
    assert payload["enable_thinking"] is False
    assert payload["max_tokens"] == 1000
    assert captured["url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    content = payload["messages"][0]["content"]
    assert [item for item in content if item.get("type") == "image_url"] == []
    prompt = next(item["text"] for item in content if item.get("type") == "text")
    assert "不要编造" in prompt
    assert "still_needed" in prompt
    assert "合同标的" in prompt
    assert "北京时序天成技术有限公司" in prompt
    monkeypatch.setenv("QWEN_API_KEY", "")
    get_settings.cache_clear()


def test_understand_image_has_no_ocr_pixel_caps_on_37(monkeypatch) -> None:
    _enable_qwen(monkeypatch)
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": '{"party_a":"甲","still_needed":["party_b"]}'}}]}

    def fake_post(_url: str, **kwargs):
        captured["json"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr("app.services.qwen_ocr.httpx.post", fake_post)
    understand_page(already=fields_from_llm_payload({}), image_jpeg=b"abc")
    content = captured["json"]["messages"][0]["content"]
    images = [item for item in content if item.get("type") == "image_url"]
    assert len(images) == 1
    assert "max_pixels" not in images[0]
    assert captured["json"]["enable_thinking"] is False
    monkeypatch.setenv("QWEN_API_KEY", "")
    get_settings.cache_clear()


def test_ocr_model_override_still_sends_pixel_caps(monkeypatch) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "sk-test")
    monkeypatch.setenv("QWEN_OCR_MODEL", "qwen3.5-ocr")
    get_settings.cache_clear()
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": "{}"}}]}

    def fake_post(_url: str, **kwargs):
        captured["json"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr("app.services.qwen_ocr.httpx.post", fake_post)
    understand_page(already=fields_from_llm_payload({}), image_jpeg=b"abc")
    images = [item for item in captured["json"]["messages"][0]["content"] if item.get("type") == "image_url"]
    assert images[0]["max_pixels"] == 32 * 32 * 1280
    monkeypatch.setenv("QWEN_OCR_MODEL", "qwen3.7-plus")
    monkeypatch.setenv("QWEN_API_KEY", "")
    get_settings.cache_clear()


def test_jpeg_for_ocr_caps_long_edge() -> None:
    image = Image.new("RGB", (2000, 2800), "white")
    jpeg = jpeg_for_ocr(image)
    out = Image.open(BytesIO(jpeg))
    assert max(out.size) <= MAX_IMAGE_SIDE


def test_understand_skipped_without_key() -> None:
    fields, needed, error = understand_page(already=fields_from_llm_payload({}), page_text="任意正文")
    assert fields.contract_no == ""
    assert needed == []
    assert error and "QWEN_API_KEY" in error
