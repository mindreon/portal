from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.services.extract import extract_fields, grouping_key, normalize_contract_no
from app.services.pdf_parse import ParsedPdf


def test_extract_without_contract_no() -> None:
    text = """
    甲方：星河科技有限公司
    乙方：本地运营主体
    合同总金额（元）：120000.00
    合同签订时间：2026年1月1日
    履约期限（起止）：2026年1月1日 至 2026年12月31日
    第一期 30%
    尾款 70%
    """
    fields = extract_fields(text)
    assert fields.contract_no == ""
    assert fields.party_a == "星河科技有限公司"
    assert fields.party_b == "本地运营主体"
    assert fields.amount == Decimal("120000.00")
    assert grouping_key(fields.contract_no, 9) == "file:9"
    assert normalize_contract_no("") is None
    assert "未编号" in fields.title or fields.warnings


def test_extract_invoice_and_number() -> None:
    text = "合同编号：HT-2026-001\n发票代码：012001900104\n发票号码：12345678\n发票金额（元）：40000"
    fields = extract_fields(text)
    assert fields.contract_no == "HT-2026-001"
    assert grouping_key(fields.contract_no, 1) == "no:HT-2026-001"
    assert fields.invoices[0].invoice_code == "012001900104"


def test_import_groups_by_number_and_keeps_unnumbered_separate(logged_in: TestClient, monkeypatch) -> None:
    texts = {
        "a.pdf": "Contract No: HT-GROUP-1 甲方：AAA 乙方：BBB 合同总金额（元）：100",
        "b.pdf": "Contract No: HT-GROUP-1 appendix 甲方：AAA 乙方：BBB",
        "c.pdf": "甲方：CCC 乙方：DDD 合同总金额（元）：50",
    }

    def fake_parse(data: bytes) -> ParsedPdf:
        return ParsedPdf(text=data.decode("utf-8"), source="electronic")

    monkeypatch.setattr("app.services.imports.parse_pdf_bytes", fake_parse)
    response = logged_in.post(
        "/api/v1/contracts/imports",
        files=[("files", (name, content.encode("utf-8"), "application/pdf")) for name, content in texts.items()],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert len(body["contracts"]) == 2
    numbered = next(item for item in body["contracts"] if item["contract_no"] == "HT-GROUP-1")
    blank = next(item for item in body["contracts"] if item["contract_no"] is None)
    numbered_files = [item for item in body["files"] if item["contract_id"] == numbered["id"]]
    assert len(numbered_files) == 2
    assert blank["party_a"] == "CCC"


def test_two_blank_contract_numbers_allowed(logged_in: TestClient) -> None:
    payload = {"title": "未编号甲", "counterparty": "客户A", "amount": "1"}
    first = logged_in.post("/api/v1/contracts", json=payload)
    second = logged_in.post("/api/v1/contracts", json={**payload, "title": "未编号乙"})
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["contract_no"] is None
    assert second.json()["id"] != first.json()["id"]


def test_zip_upload(logged_in: TestClient, monkeypatch) -> None:
    def fake_parse(data: bytes) -> ParsedPdf:
        return ParsedPdf(text=data.decode("utf-8"), source="electronic")

    monkeypatch.setattr("app.services.imports.parse_pdf_bytes", fake_parse)
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("inner.pdf", "合同编号：HT-ZIP-1 甲方：AAA 乙方：BBB".encode("utf-8"))
    response = logged_in.post(
        "/api/v1/contracts/imports",
        files=[("files", ("pack.zip", buffer.getvalue(), "application/zip"))],
    )
    assert response.status_code == 201, response.text
    assert response.json()["contracts"][0]["contract_no"] == "HT-ZIP-1"


def test_collection_and_schedule(logged_in: TestClient) -> None:
    created = logged_in.post(
        "/api/v1/contracts",
        json={"title": "回款合同", "contract_no": "HT-PAY", "counterparty": "客户", "amount": "100"},
    )
    contract_id = created.json()["id"]
    assert logged_in.get(f"/api/v1/contracts/{contract_id}/schedules").status_code == 200
    added = logged_in.post(
        f"/api/v1/contracts/{contract_id}/schedules",
        json={"name": "尾款", "amount": "40"},
    )
    assert added.status_code == 201
    paid = logged_in.post(
        f"/api/v1/contracts/{contract_id}/collections",
        json={"amount": "40", "received_at": "2026-02-01", "schedule_id": added.json()["id"]},
    )
    assert paid.status_code == 201
    detail = logged_in.get(f"/api/v1/contracts/{contract_id}")
    assert detail.json()["collected_amount"] == "40.00"
