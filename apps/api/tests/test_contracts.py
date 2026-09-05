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


def test_schedule_and_collection_can_be_edited(logged_in: TestClient) -> None:
    created = logged_in.post(
        "/api/v1/contracts",
        json={"title": "可改回款", "contract_no": "HT-EDIT-PAY", "counterparty": "客户", "amount": "100"},
    )
    contract_id = created.json()["id"]
    schedule = logged_in.post(
        f"/api/v1/contracts/{contract_id}/schedules",
        json={"name": "首付款", "amount": "30"},
    ).json()
    other = logged_in.post(
        f"/api/v1/contracts/{contract_id}/schedules",
        json={"name": "尾款", "amount": "70"},
    ).json()

    renamed = logged_in.put(
        f"/api/v1/contracts/{contract_id}/schedules/{schedule['id']}",
        json={"name": "预付款", "amount": "40"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "预付款"
    assert renamed.json()["amount"] == "40.00"

    paid = logged_in.post(
        f"/api/v1/contracts/{contract_id}/collections",
        json={"amount": "10", "received_at": "2026-09-01", "schedule_id": schedule["id"]},
    )
    assert paid.status_code == 201
    collection_id = paid.json()["id"]

    blocked = logged_in.delete(f"/api/v1/contracts/{contract_id}/schedules/{schedule['id']}")
    assert blocked.status_code == 409

    updated = logged_in.put(
        f"/api/v1/contracts/{contract_id}/collections/{collection_id}",
        json={"amount": "25", "received_at": "2026-09-05", "schedule_id": other["id"]},
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == "25.00"
    assert updated.json()["received_at"] == "2026-09-05"
    assert updated.json()["schedule_id"] == other["id"]
    assert logged_in.get(f"/api/v1/contracts/{contract_id}").json()["collected_amount"] == "25.00"

    foreign = logged_in.post(
        "/api/v1/contracts",
        json={"title": "另一份", "contract_no": "HT-OTHER", "counterparty": "别人", "amount": "1"},
    ).json()
    foreign_schedule = logged_in.post(
        f"/api/v1/contracts/{foreign['id']}/schedules",
        json={"name": "别人的期", "amount": "1"},
    ).json()
    wrong_schedule = logged_in.put(
        f"/api/v1/contracts/{contract_id}/collections/{collection_id}",
        json={"amount": "25", "schedule_id": foreign_schedule["id"]},
    )
    assert wrong_schedule.status_code == 400

    removed = logged_in.delete(f"/api/v1/contracts/{contract_id}/collections/{collection_id}")
    assert removed.status_code == 204
    assert logged_in.get(f"/api/v1/contracts/{contract_id}").json()["collected_amount"] == "0"
    assert logged_in.delete(f"/api/v1/contracts/{contract_id}/schedules/{schedule['id']}").status_code == 204
    missing = logged_in.delete(f"/api/v1/contracts/{contract_id}/collections/{collection_id}")
    assert missing.status_code == 404


def test_duplicate_contract_no(logged_in: TestClient) -> None:
    payload = {
        "title": "A",
        "contract_no": "HT-DUP",
        "counterparty": "B",
        "amount": "1",
    }
    assert logged_in.post("/api/v1/contracts", json=payload).status_code == 201
    assert logged_in.post("/api/v1/contracts", json=payload).status_code == 409
