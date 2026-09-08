from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.user import User
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


def test_member_cannot_list_or_patch_users(member_client: TestClient) -> None:
    assert member_client.get("/api/v1/users").status_code == 403
    assert member_client.patch("/api/v1/users/1", json={"modules": ["invoices"]}).status_code == 403


def test_admin_lists_users_and_grants_contracts(logged_in: TestClient) -> None:
    from app.core.security import create_session_token
    from app.main import app

    db = SessionLocal()
    try:
        staff = User(
            name="普通员工",
            email="staff@localhost",
            role="member",
            feishu_open_id="ou_staff_grant",
            modules="invoices",
        )
        db.add(staff)
        db.commit()
        db.refresh(staff)
        staff_id = staff.id
        token = create_session_token(staff.id)
    finally:
        db.close()

    listed = logged_in.get("/api/v1/users")
    assert listed.status_code == 200
    people = listed.json()
    assert any(item["id"] == staff_id and item["modules"] == ["invoices"] for item in people)

    patched = logged_in.patch(f"/api/v1/users/{staff_id}", json={"modules": ["contracts", "invoices"]})
    assert patched.status_code == 200
    assert patched.json()["modules"] == ["contracts", "invoices"]

    member = TestClient(app)
    member.cookies.set(get_settings().cookie_name, token)
    assert member.get("/api/v1/contracts").status_code == 200


def test_cannot_demote_last_admin(logged_in: TestClient) -> None:
    me = logged_in.get("/api/v1/auth/me").json()
    response = logged_in.patch(f"/api/v1/users/{me['id']}", json={"role": "member"})
    assert response.status_code == 400
    assert "管理员" in response.json()["detail"]


def test_unknown_module_rejected(logged_in: TestClient) -> None:
    me = logged_in.get("/api/v1/auth/me").json()
    response = logged_in.patch(f"/api/v1/users/{me['id']}", json={"modules": ["payroll"]})
    assert response.status_code == 400


def test_feishu_allowlist_promotes_new_user(monkeypatch) -> None:
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
        assert admin.modules == "contracts,invoices"
        assert member.role == "member"
        assert member.modules == "invoices"
    finally:
        db.close()
        get_settings.cache_clear()


def test_feishu_login_keeps_modules_from_admin_page() -> None:
    """权限页勾选之后，对方再登录不应该被 .env 改回去。"""
    db = SessionLocal()
    try:
        user = upsert_feishu_user(
            db,
            FeishuProfile(
                open_id="ou_staff",
                union_id=None,
                name="员工",
                email="staff@company.com",
                avatar_url=None,
            ),
        )
        # 第一个人会变成管理员（库里还没有管理员）。这里改成普通成员并只给发票，模拟权限页操作。
        row = db.get(User, user.id)
        assert row is not None
        row.role = "member"
        row.modules = "invoices"
        db.commit()

        again = upsert_feishu_user(
            db,
            FeishuProfile(
                open_id="ou_staff",
                union_id=None,
                name="员工改名",
                email="staff@company.com",
                avatar_url=None,
            ),
        )
        assert again.role == "member"
        assert again.modules == "invoices"
        assert again.name == "员工改名"
    finally:
        db.close()
