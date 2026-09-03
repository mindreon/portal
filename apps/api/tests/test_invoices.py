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
