from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_tenant():
    response = client.get(
        "/tenants/me",
        headers={"X-Tenant-Key": "tenant-001"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tenant_key"] == "tenant-001"
    assert data["name"] == "Demo Tenant One"
    assert data["status"] == "active"
    assert data["plan_code"] == "free"
    assert data["api_call_limit"] == 1000
    assert data["ai_token_limit"] == 100000


def test_missing_tenant_header():
    response = client.get("/tenants/me")

    assert response.status_code == 400
    assert response.json()["detail"] == "X-Tenant-Key header is required."


def test_unknown_tenant():
    response = client.get(
        "/tenants/me",
        headers={"X-Tenant-Key": "tenant-does-not-exist"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found."