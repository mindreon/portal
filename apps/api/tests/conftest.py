"""
测试用独立的 SQLite 内存库，避免碰到开发者电脑上的真实数据。

每个测试函数拿到一个 FastAPI TestClient，它能带着 Cookie 连续发请求。
"""

import os

# 必须在导入 app 之前设置，否则 Settings 会读到默认 Postgres
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes-long")
os.environ.setdefault("AUTH_ALLOW_DEV_LOGIN", "true")
os.environ.setdefault("FEISHU_APP_ID", "")
os.environ.setdefault("UPLOAD_DIR", "/tmp/portal-test-uploads")
os.environ.setdefault("QWEN_API_KEY", "")
os.environ.setdefault("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
os.environ.setdefault("QWEN_OCR_MODEL", "qwen3.7-plus")

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.services.jobs import wait_all_imports


@pytest.fixture(autouse=True)
def reset_db() -> Generator[None, None, None]:
    get_settings.cache_clear()
    try:
        wait_all_imports(timeout=5)
    except Exception:
        pass
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    upload_dir = Path(os.environ["UPLOAD_DIR"])
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    yield
    try:
        wait_all_imports(timeout=20)
    except Exception:
        pass
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def logged_in(client: TestClient) -> TestClient:
    response = client.post("/api/v1/auth/dev-login", json={"name": "测试管理员"})
    assert response.status_code == 200
    return client


@pytest.fixture
def member_client(client: TestClient) -> TestClient:
    """飞书普通员工：能登录、能看发票，不能进合同接口。"""
    from app.core.security import create_session_token
    from app.db.session import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        user = User(name="普通员工", email="staff@localhost", role="member", feishu_open_id="ou_member")
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_session_token(user.id)
    finally:
        db.close()
    client.cookies.set(get_settings().cookie_name, token)
    return client
