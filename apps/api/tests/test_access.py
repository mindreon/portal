from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.auth import upsert_feishu_user
from app.services.feishu import FeishuProfile


def test_member_me_only_has_invoices(member_client: TestClient) -> None:
    body = member_client.get("/api/v1/auth/me").json()
    assert body["role"] == "member"
    assert body["modules"] == ["invoices"]


def test_member_can_use_invoices(member_client: TestClient) -> None:
    listed = member_client.get("/api/v1/invoices")
    assert listed.status_code == 200
    created = member_client.post(
        "/api/v1/invoices",
        json={
            "title": "员工开的发票",
            "invoice_no": "FP-STAFF-1",
            "counterparty": "客户",
            "amount": "100",
        },
    )
    assert created.status_code == 201


def test_member_cannot_open_contracts(member_client: TestClient) -> None:
    listed = member_client.get("/api/v1/contracts")
    assert listed.status_code == 403
    assert listed.json()["detail"] == "没有访问该模块的权限"

    created = member_client.post(
        "/api/v1/contracts",
        json={"title": "不该创建", "counterparty": "客户", "amount": "1"},
    )
    assert created.status_code == 403

    imported = member_client.get("/api/v1/contracts/imports/files/1/download")
    assert imported.status_code == 403


def test_admin_still_opens_contracts(logged_in: TestClient) -> None:
    response = logged_in.get("/api/v1/contracts")
    assert response.status_code == 200


def test_feishu_allowlist_controls_admin_role(monkeypatch) -> None:
    """飞书只负责认出人；谁当管理员由我们 .env 里的邮箱名单决定。"""
    monkeypatch.setenv("AUTH_ADMIN_EMAILS", "boss@company.com")
    get_settings.cache_clear()
    db = SessionLocal()
    try:
        admin = upsert_feishu_user(
            db,
            FeishuProfile(
                open_id="ou_boss",
                union_id=None,
                name="老板",
                email="boss@company.com",
                avatar_url=None,
            ),
        )
        member = upsert_feishu_user(
            db,
            FeishuProfile(
                open_id="ou_staff",
                union_id=None,
                name="员工",
                email="staff@company.com",
                avatar_url=None,
            ),
        )
        assert admin.role == "admin"
        assert member.role == "member"

        monkeypatch.setenv("AUTH_ADMIN_EMAILS", "")
        get_settings.cache_clear()
        demoted = upsert_feishu_user(
            db,
            FeishuProfile(
                open_id="ou_boss",
                union_id=None,
                name="老板",
                email="boss@company.com",
                avatar_url=None,
            ),
        )
        assert demoted.role == "member"
    finally:
        db.close()
        get_settings.cache_clear()
