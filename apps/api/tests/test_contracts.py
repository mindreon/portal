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
    assert listed.json()["total"] == 1
    assert len(listed.json()["items"]) == 1

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
    empty = logged_in.get("/api/v1/contracts").json()
    assert empty["items"] == []
    assert empty["total"] == 0


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


def test_subject_name_and_inferred_our_role(logged_in: TestClient) -> None:
    created = logged_in.post(
        "/api/v1/contracts",
        json={
            "title": "软件产品销售合同",
            "party_a": "医大一",
            "party_b": "深圳市迈能同行科技有限公司",
            "subject_name": "AI 调度软件",
            "amount": "100000",
            "status": "active",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["subject_name"] == "AI 调度软件"
    assert body["our_role"] == "party_b"
    assert body["counterparty"] == "医大一"
    assert body["account_kind"] == "receivable"


def test_receivable_and_payable_are_summarized_separately(logged_in: TestClient) -> None:
    sale = logged_in.post(
        "/api/v1/contracts",
        json={
            "title": "销售合同",
            "contract_no": "HT-AR",
            "party_a": "医大一",
            "party_b": "深圳市迈能同行科技有限公司",
            "amount": "100000",
            "status": "active",
        },
    )
    buy = logged_in.post(
        "/api/v1/contracts",
        json={
            "title": "采购合同",
            "contract_no": "HT-AP",
            "party_a": "深圳市迈能同行科技有限公司",
            "party_b": "某供应商",
            "amount": "30000",
            "status": "active",
        },
    )
    other = logged_in.post(
        "/api/v1/contracts",
        json={
            "title": "无关合同",
            "contract_no": "HT-OTHER-KIND",
            "party_a": "甲公司",
            "party_b": "乙公司",
            "amount": "9000",
            "status": "draft",
        },
    )
    assert sale.status_code == 201, sale.text
    assert sale.json()["account_kind"] == "receivable"
    assert buy.json()["account_kind"] == "payable"
    assert other.json()["account_kind"] == ""

    assert (
        logged_in.post(
            f"/api/v1/contracts/{sale.json()['id']}/collections",
            json={"amount": "40000", "received_at": "2026-03-01"},
        ).status_code
        == 201
    )
    assert (
        logged_in.post(
            f"/api/v1/contracts/{buy.json()['id']}/collections",
            json={"amount": "10000", "received_at": "2026-03-02"},
        ).status_code
        == 201
    )

    summary = logged_in.get("/api/v1/contracts/summary").json()
    assert summary["receivable_amount"] == "100000.00"
    assert summary["receivable_collected"] == "40000.00"
    assert summary["receivable_outstanding"] == "60000.00"
    assert summary["payable_amount"] == "30000.00"
    assert summary["payable_paid"] == "10000.00"
    assert summary["payable_outstanding"] == "20000.00"
    # 待回款不能把采购合同金额混进来：100000-40000=60000，而不是 139000-50000。
    assert summary["outstanding_amount"] == "60000.00"

    only_ar = logged_in.get("/api/v1/contracts", params={"account_kind": "receivable"}).json()
    assert only_ar["total"] == 1
    assert only_ar["items"][0]["contract_no"] == "HT-AR"
    only_ap = logged_in.get("/api/v1/contracts", params={"account_kind": "payable"}).json()
    assert only_ap["total"] == 1
    assert only_ap["items"][0]["contract_no"] == "HT-AP"

    payments = logged_in.get("/api/v1/contracts/payments").json()
    assert payments["receivable_count"] == 1
    assert payments["receivable_amount"] == "40000.00"
    assert payments["payable_count"] == 1
    assert payments["payable_amount"] == "10000.00"
    assert payments["total"] == 2
    assert {item["account_kind"] for item in payments["items"]} == {"receivable", "payable"}

    only_in = logged_in.get("/api/v1/contracts/payments", params={"kind": "receivable"}).json()
    assert only_in["total"] == 1
    assert only_in["items"][0]["account_kind"] == "receivable"
    assert only_in["receivable_amount"] == "40000.00"
    assert only_in["payable_amount"] == "10000.00"
    only_out = logged_in.get("/api/v1/contracts/payments", params={"kind": "payable"}).json()
    assert only_out["total"] == 1
    assert only_out["items"][0]["account_kind"] == "payable"


def test_contract_list_paginates_and_searches(logged_in: TestClient) -> None:
    for index in range(12):
        created = logged_in.post(
            "/api/v1/contracts",
            json={
                "title": f"分页合同{index:02d}",
                "contract_no": f"HT-PAGE-{index:02d}",
                "counterparty": "示例客户",
                "amount": "1",
            },
        )
        assert created.status_code == 201, created.text

    first = logged_in.get("/api/v1/contracts", params={"page": 1, "page_size": 10})
    assert first.status_code == 200
    body = first.json()
    assert body["total"] == 12
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) == 10

    second = logged_in.get("/api/v1/contracts", params={"page": 2, "page_size": 10})
    assert len(second.json()["items"]) == 2
    assert second.json()["total"] == 12

    huge = logged_in.get("/api/v1/contracts", params={"page_size": 200})
    assert huge.json()["page_size"] == 100
    assert len(huge.json()["items"]) == 12

    hit = logged_in.get("/api/v1/contracts", params={"q": "HT-PAGE-11"})
    assert hit.json()["total"] == 1
    assert hit.json()["items"][0]["contract_no"] == "HT-PAGE-11"

    summary = logged_in.get("/api/v1/contracts/summary")
    assert summary.status_code == 200
    assert summary.json()["count"] == 12
    assert summary.json()["parsing_count"] == 0


def test_payment_list_paginates_and_searches(logged_in: TestClient) -> None:
    created = logged_in.post(
        "/api/v1/contracts",
        json={"title": "回款分页", "contract_no": "HT-PAY-PAGE", "counterparty": "客户", "amount": "100"},
    )
    contract_id = created.json()["id"]
    for index in range(12):
        paid = logged_in.post(
            f"/api/v1/contracts/{contract_id}/collections",
            json={"amount": "1", "received_at": f"2026-01-{index + 1:02d}"},
        )
        assert paid.status_code == 201, paid.text

    first = logged_in.get("/api/v1/contracts/payments", params={"page": 1, "page_size": 10})
    assert first.status_code == 200
    body = first.json()
    assert body["total"] == 12
    assert len(body["items"]) == 10
    assert body["total_amount"] == "12.00"

    second = logged_in.get("/api/v1/contracts/payments", params={"page": 2, "page_size": 10})
    assert len(second.json()["items"]) == 2

    hit = logged_in.get("/api/v1/contracts/payments", params={"q": "回款分页"})
    assert hit.json()["total"] == 12
    miss = logged_in.get("/api/v1/contracts/payments", params={"q": "不存在的合同"})
    assert miss.json()["items"] == []
    assert miss.json()["total"] == 0
