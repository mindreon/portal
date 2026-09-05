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
os.environ.setdefault("QWEN_OCR_MODEL", "qwen3.5-ocr")

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db() -> Generator[None, None, None]:
    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def logged_in(client: TestClient) -> TestClient:
    response = client.post("/api/v1/auth/dev-login", json={"name": "测试管理员"})
    assert response.status_code == 200
    return client
