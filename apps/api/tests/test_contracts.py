from fastapi.testclient import TestClient


def test_contract_crud(logged_in: TestClient) -> None:
    created = logged_in.post(
        "/api/v1/contracts",
        json={
            "title": "软件开发合同",
            "contract_no": "HT-2026-001",
            "counterparty": "示例客户",
            "amount": "120000.00",
            "status": "active",
        },
    )
    assert created.status_code == 201
    contract_id = created.json()["id"]

    listed = logged_in.get("/api/v1/contracts")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = logged_in.put(
        f"/api/v1/contracts/{contract_id}",
        json={
            "title": "软件开发合同（修订）",
            "contract_no": "HT-2026-001",
            "counterparty": "示例客户",
            "amount": "150000.00",
            "status": "active",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == "150000.00"

    deleted = logged_in.delete(f"/api/v1/contracts/{contract_id}")
    assert deleted.status_code == 204
    assert logged_in.get("/api/v1/contracts").json() == []


def test_duplicate_contract_no(logged_in: TestClient) -> None:
    payload = {
        "title": "A",
        "contract_no": "HT-DUP",
        "counterparty": "B",
        "amount": "1",
    }
    assert logged_in.post("/api/v1/contracts", json=payload).status_code == 201
    assert logged_in.post("/api/v1/contracts", json=payload).status_code == 409
