import os
import threading
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.services.extract import ExtractedFields
from app.services.jobs import wait_import
from app.services.pdf_parse import ParsedPdf


def _parse_with(fields: ExtractedFields):
    def fake_parse(data: bytes) -> ParsedPdf:
        return ParsedPdf(text=data.decode("utf-8"), source="electronic", fields=fields)

    return fake_parse


def _parse_map(mapping: dict[str, ExtractedFields]):
    def fake_parse(data: bytes) -> ParsedPdf:
        text = data.decode("utf-8")
        return ParsedPdf(text=text, source="electronic", fields=mapping[text])

    return fake_parse


def _wait_import(client: TestClient, response) -> dict:
    assert response.status_code == 201, response.text
    batch_id = response.json()["id"]
    wait_import(batch_id)
    detail = client.get(f"/api/v1/contracts/imports/{batch_id}")
    assert detail.status_code == 200, detail.text
    return detail.json()


def test_import_groups_by_number_and_keeps_unnumbered_separate(logged_in: TestClient, monkeypatch) -> None:
    texts = {
        "a.pdf": "a-group",
        "b.pdf": "b-group-appendix",
        "c.pdf": "c-unnumbered",
    }
    monkeypatch.setattr(
        "app.services.imports.parse_pdf_bytes",
        _parse_map(
            {
                "a-group": ExtractedFields(
                    doc_type="contract", contract_no="HT-GROUP-1", party_a="AAA", party_b="BBB", amount=Decimal("100")
                ),
                "b-group-appendix": ExtractedFields(
                    doc_type="contract", contract_no="HT-GROUP-1", party_a="AAA", party_b="BBB"
                ),
                "c-unnumbered": ExtractedFields(
                    doc_type="contract", party_a="CCC", party_b="DDD", amount=Decimal("50")
                ),
            }
        ),
    )
    response = logged_in.post(
        "/api/v1/contracts/imports",
        files=[("files", (name, content.encode("utf-8"), "application/pdf")) for name, content in texts.items()],
    )
    # 上传当下就有三份占位合同，识别完成后再按编号合成两份
    assert response.status_code == 201, response.text
    assert len(response.json()["contracts"]) == 3
    body = _wait_import(logged_in, response)
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


def test_zip_upload_extracts_to_separate_pdf(logged_in: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.imports.parse_pdf_bytes",
        _parse_with(ExtractedFields(doc_type="contract", contract_no="HT-ZIP-1", party_a="AAA", party_b="BBB")),
    )
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("inner.pdf", "合同编号：HT-ZIP-1 甲方：AAA 乙方：BBB".encode())
    response = logged_in.post(
        "/api/v1/contracts/imports",
        files=[("files", ("pack.zip", buffer.getvalue(), "application/zip"))],
    )
    body = _wait_import(logged_in, response)
    assert body["contracts"][0]["contract_no"] == "HT-ZIP-1"
    assert body["contracts"][0]["source_filename"] == "pack/inner.pdf"
    upload_root = Path(os.environ["UPLOAD_DIR"]) / str(body["id"])
    pdfs = list(upload_root.glob("*.pdf"))
    zips = list(upload_root.glob("*.zip"))
    assert len(pdfs) == 1
    assert zips == []


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

    summary = logged_in.get("/api/v1/contracts/summary")
    assert summary.status_code == 200
    assert summary.json()["count"] >= 1
    payments = logged_in.get("/api/v1/contracts/payments")
    assert payments.status_code == 200
    assert payments.json()[0]["contract_no"] == "HT-PAY"
    filtered = logged_in.get("/api/v1/contracts", params={"party": "客户"})
    assert filtered.status_code == 200
    assert any(item["contract_no"] == "HT-PAY" for item in filtered.json())
    miss = logged_in.get("/api/v1/contracts", params={"party": "不存在的主体"})
    assert miss.json() == []


def test_duplicate_bytes_do_not_create_second_contract(logged_in: TestClient, monkeypatch) -> None:
    payload = "same-bytes-payload"
    monkeypatch.setattr(
        "app.services.imports.parse_pdf_bytes",
        _parse_with(
            ExtractedFields(
                doc_type="contract",
                party_a="星河科技有限公司",
                party_b="本地运营主体",
                amount=Decimal("120000.00"),
                signed_at=date(2026, 1, 1),
            )
        ),
    )
    files = [("files", ("same.pdf", payload.encode("utf-8"), "application/pdf"))]
    first = logged_in.post("/api/v1/contracts/imports", files=files)
    _wait_import(logged_in, first)
    second = logged_in.post("/api/v1/contracts/imports", files=files)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert len(first.json()["contracts"]) == 1
    assert len(first.json()["files"]) == 1
    assert len(second.json()["files"]) == 0
    assert second.json()["contracts"][0]["id"] == first.json()["contracts"][0]["id"]
    assert "内容相同" in (second.json()["warning_text"] or "")
    listing = logged_in.get("/api/v1/contracts")
    matches = [item for item in listing.json() if item["party_a"] == "星河科技有限公司"]
    assert len(matches) == 1


def test_same_batch_duplicate_bytes_kept_once(logged_in: TestClient, monkeypatch) -> None:
    payload = "same-batch-bytes"
    monkeypatch.setattr(
        "app.services.imports.parse_pdf_bytes",
        _parse_with(
            ExtractedFields(
                doc_type="contract",
                party_a="甲公司",
                party_b="乙公司",
                amount=Decimal("10"),
                signed_at=date(2026, 2, 2),
            )
        ),
    )
    blob = payload.encode("utf-8")
    response = logged_in.post(
        "/api/v1/contracts/imports",
        files=[
            ("files", ("one.pdf", blob, "application/pdf")),
            ("files", ("copy.pdf", blob, "application/pdf")),
        ],
    )
    body = _wait_import(logged_in, response)
    assert len(body["contracts"]) == 1
    assert len(body["files"]) == 1
    assert "内容相同" in (body["warning_text"] or "")


def test_unnumbered_fingerprint_merges_different_scans(logged_in: TestClient, monkeypatch) -> None:
    fields = ExtractedFields(
        doc_type="contract",
        party_a="甲公司",
        party_b="乙公司",
        amount=Decimal("88.00"),
        signed_at=date(2026, 3, 3),
    )
    monkeypatch.setattr("app.services.imports.parse_pdf_bytes", _parse_with(fields))
    first = logged_in.post(
        "/api/v1/contracts/imports",
        files=[("files", ("scan-a.pdf", b"scan-a-original", "application/pdf"))],
    )
    first_body = _wait_import(logged_in, first)
    second = logged_in.post(
        "/api/v1/contracts/imports",
        files=[("files", ("scan-b.pdf", b"scan-b-copy", "application/pdf"))],
    )
    second_body = _wait_import(logged_in, second)
    assert second_body["contracts"][0]["id"] == first_body["contracts"][0]["id"]
    assert "已并入" in (second_body["warning_text"] or "")
    files = logged_in.get(f"/api/v1/contracts/{first_body['contracts'][0]['id']}/files")
    assert len(files.json()) == 2


def test_preview_is_inline_and_download_is_attachment(logged_in: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.imports.parse_pdf_bytes",
        _parse_with(ExtractedFields(doc_type="contract", party_a="甲", party_b="乙")),
    )
    created = logged_in.post(
        "/api/v1/contracts/imports",
        files=[("files", ("preview.pdf", "甲方：甲\n乙方：乙".encode(), "application/pdf"))],
    )
    file_id = created.json()["files"][0]["id"]
    preview = logged_in.get(f"/api/v1/contracts/imports/files/{file_id}/preview")
    download = logged_in.get(f"/api/v1/contracts/imports/files/{file_id}/download")
    assert preview.status_code == 200
    assert download.status_code == 200
    assert preview.headers["content-type"].startswith("application/pdf")
    assert "inline" in preview.headers["content-disposition"]
    assert "attachment" in download.headers["content-disposition"]


def test_upload_returns_placeholders_then_list_shows_filename(logged_in: TestClient, monkeypatch) -> None:
    started = threading.Event()
    release = threading.Event()

    def slow_parse(data: bytes) -> ParsedPdf:
        started.set()
        assert release.wait(timeout=5)
        return ParsedPdf(
            text=data.decode("utf-8"),
            source="electronic",
            fields=ExtractedFields(doc_type="contract", contract_no="HT-ASYNC-1", party_a="甲", party_b="乙"),
        )

    monkeypatch.setattr("app.services.imports.parse_pdf_bytes", slow_parse)
    try:
        response = logged_in.post(
            "/api/v1/contracts/imports",
            files=[("files", ("采购合同.pdf", b"async-contract-bytes", "application/pdf"))],
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] == "processing"
        assert body["contracts"][0]["source_filename"] == "采购合同.pdf"
        assert body["contracts"][0]["parse_status"] in {"pending", "processing"}
        assert body["files"][0]["parse_status"] in {"pending", "processing"}
        listing = logged_in.get("/api/v1/contracts")
        assert listing.status_code == 200
        row = listing.json()[0]
        assert row["source_filename"] == "采购合同.pdf"
        assert row["parse_status"] in {"pending", "processing"}
        assert started.wait(timeout=5)
    finally:
        release.set()
    done = _wait_import(logged_in, response)
    assert done["status"] == "review"
    assert done["contracts"][0]["contract_no"] == "HT-ASYNC-1"
    listing = logged_in.get("/api/v1/contracts")
    row = listing.json()[0]
    assert row["parse_status"] == "done"
    assert row["source_filename"] == "采购合同.pdf"
    by_name = logged_in.get("/api/v1/contracts", params={"party": "采购合同"})
    assert any(item["id"] == row["id"] for item in by_name.json())
