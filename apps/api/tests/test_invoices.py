from fastapi.testclient import TestClient


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
