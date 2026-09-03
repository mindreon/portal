from fastapi.testclient import TestClient


def test_auth_config_without_feishu(client: TestClient) -> None:
    response = client.get("/api/v1/auth/config")
    assert response.status_code == 200
    body = response.json()
    assert body["feishu_enabled"] is False
    assert body["dev_login_enabled"] is True


def test_me_requires_login(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_dev_login_and_me(client: TestClient) -> None:
    login = client.post("/api/v1/auth/dev-login", json={"name": "王同学"})
    assert login.status_code == 200
    assert login.json()["name"] == "王同学"
    assert login.json()["role"] == "admin"

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["name"] == "王同学"


def test_logout(logged_in: TestClient) -> None:
    response = logged_in.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert logged_in.get("/api/v1/auth/me").status_code == 401


def test_feishu_login_without_config(client: TestClient) -> None:
    response = client.get("/api/v1/auth/feishu/login")
    assert response.status_code == 400
