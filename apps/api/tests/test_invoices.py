from pathlib import Path

from fastapi.testclient import TestClient

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
OTHER_PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Other true>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"


def _upload(client: TestClient, files: list[tuple[str, bytes]], contract_id: int | None = None):
    payload = [("files", (name, data, "application/pdf")) for name, data in files]
    data = {"contract_id": str(contract_id)} if contract_id is not None else None
    return client.post("/api/v1/invoices/upload", files=payload, data=data)


def test_invoice_with_contract(logged_in: TestClient) -> None:
    contract = logged_in.post(
        "/api/v1/contracts",
        json={
            "title": "顾问合同",
            "contract_no": "HT-INV-1",
            "counterparty": "顾问公司",
            "amount": "80000",
        },
    )
    contract_id = contract.json()["id"]

    created = logged_in.post(
        "/api/v1/invoices",
        json={
            "title": "首期款发票",
            "invoice_no": "FP-2026-001",
            "counterparty": "顾问公司",
            "amount": "40000",
            "tax_amount": "2400",
            "status": "issued",
            "contract_id": contract_id,
        },
    )
    assert created.status_code == 201
    assert created.json()["contract_id"] == contract_id

    missing = logged_in.post(
        "/api/v1/invoices",
        json={
            "title": "坏关联",
            "invoice_no": "FP-BAD",
            "counterparty": "顾问公司",
            "amount": "1",
            "contract_id": 9999,
        },
    )
    assert missing.status_code == 400


def test_invoice_list_paginates_and_filters(logged_in: TestClient) -> None:
    contract = logged_in.post(
        "/api/v1/contracts",
        json={"title": "关联合同", "contract_no": "HT-INV-PAGE", "counterparty": "客户", "amount": "1"},
    )
    contract_id = contract.json()["id"]
    for index in range(12):
        created = logged_in.post(
            "/api/v1/invoices",
            json={
                "title": f"分页发票{index:02d}",
                "invoice_no": f"FP-PAGE-{index:02d}",
                "counterparty": "客户",
                "amount": "10",
                "status": "issued" if index < 3 else "draft",
                "contract_id": contract_id if index == 0 else None,
            },
        )
        assert created.status_code == 201, created.text

    first = logged_in.get("/api/v1/invoices", params={"page": 1, "page_size": 10})
    body = first.json()
    assert body["total"] == 12
    assert len(body["items"]) == 10

    second = logged_in.get("/api/v1/invoices", params={"page": 2, "page_size": 10})
    assert len(second.json()["items"]) == 2

    hit = logged_in.get("/api/v1/invoices", params={"q": "FP-PAGE-00"})
    assert hit.json()["total"] == 1
    assert hit.json()["items"][0]["invoice_no"] == "FP-PAGE-00"

    linked = logged_in.get("/api/v1/invoices", params={"contract_id": contract_id})
    assert linked.json()["total"] == 1
    assert linked.json()["items"][0]["contract_id"] == contract_id

    summary = logged_in.get("/api/v1/invoices/summary")
    assert summary.status_code == 200
    assert summary.json()["count"] == 12
    assert summary.json()["issued_count"] == 3


def test_upload_multiple_invoice_pdfs_and_preview(logged_in: TestClient) -> None:
    contract = logged_in.post(
        "/api/v1/contracts",
        json={"title": "软件采购协议", "contract_no": "HT-INV-PDF", "counterparty": "客户", "amount": "200000"},
    )
    contract_id = contract.json()["id"]

    uploaded = _upload(
        logged_in,
        [("第一张发票.pdf", MINIMAL_PDF), ("第二张发票.pdf", OTHER_PDF)],
        contract_id,
    )
    assert uploaded.status_code == 201, uploaded.text
    items = uploaded.json()["items"]
    assert len(items) == 2
    assert all(item["has_file"] for item in items)
    assert all(item["contract_id"] == contract_id for item in items)
    assert {item["original_name"] for item in items} == {"第一张发票.pdf", "第二张发票.pdf"}

    first = items[0]
    preview = logged_in.get(f"/api/v1/invoices/{first['id']}/preview")
    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("application/pdf")
    assert preview.content.startswith(b"%PDF")

    download = logged_in.get(f"/api/v1/invoices/{first['id']}/download")
    assert download.status_code == 200
    assert "attachment" in download.headers.get("content-disposition", "")

    duplicate = _upload(logged_in, [("第一张发票-再传.pdf", MINIMAL_PDF)], contract_id)
    assert duplicate.status_code == 400
    assert "已经上传过" in duplicate.json()["detail"]

    listed = logged_in.get("/api/v1/invoices", params={"contract_id": contract_id})
    assert listed.json()["total"] == 2

    deleted = logged_in.delete(f"/api/v1/invoices/{first['id']}")
    assert deleted.status_code == 204
    leftover = logged_in.get("/api/v1/invoices", params={"contract_id": contract_id})
    assert leftover.json()["total"] == 1
    missing = logged_in.get(f"/api/v1/invoices/{first['id']}/preview")
    assert missing.status_code == 404
    folder = Path("/tmp/portal-test-uploads") / "invoices" / str(first["id"])
    assert not folder.exists() or not any(folder.iterdir())


def test_attach_pdf_to_existing_invoice(logged_in: TestClient) -> None:
    created = logged_in.post(
        "/api/v1/invoices",
        json={"title": "后补文件", "invoice_no": "FP-ATTACH-1", "counterparty": "客户", "amount": "10"},
    )
    invoice_id = created.json()["id"]
    assert created.json()["has_file"] is False

    attached = logged_in.post(
        f"/api/v1/invoices/{invoice_id}/file",
        files={"file": ("后补.pdf", MINIMAL_PDF, "application/pdf")},
    )
    assert attached.status_code == 200, attached.text
    assert attached.json()["has_file"] is True
    assert attached.json()["original_name"] == "后补.pdf"

    rejected = logged_in.post(
        f"/api/v1/invoices/{invoice_id}/file",
        files={"file": ("不是发票.txt", b"hello", "text/plain")},
    )
    assert rejected.status_code == 400


def test_member_can_upload_invoice_pdf(member_client: TestClient) -> None:
    uploaded = _upload(member_client, [("员工发票.pdf", MINIMAL_PDF)])
    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["items"][0]["has_file"] is True
