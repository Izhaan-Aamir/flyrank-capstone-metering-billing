from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_creates_usage_event():
    response = client.post(
        "/generate",
        headers={
            "X-Tenant-Key": "tenant-001",
            "Idempotency-Key": "stage3-test-001",
        },
        json={
            "input_tokens": 1000,
            "cached_input_tokens": 200,
            "output_tokens": 500,
            "reasoning_tokens": 100,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tenant_key"] == "tenant-001"
    assert data["usage_type"] == "ai_tokens"
    assert data["quantity"] == 1600
    assert data["input_tokens"] == 1000
    assert data["cached_input_tokens"] == 200
    assert data["output_tokens"] == 500
    assert data["reasoning_tokens"] == 100


def test_same_idempotency_key_returns_same_event():
    headers = {
        "X-Tenant-Key": "tenant-001",
        "Idempotency-Key": "stage3-test-002",
    }

    payload = {
        "input_tokens": 1000,
        "cached_input_tokens": 300,
        "output_tokens": 500,
        "reasoning_tokens": 200,
    }

    first_response = client.post(
        "/generate",
        headers=headers,
        json=payload,
    )

    second_response = client.post(
        "/generate",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert second_response.json() == first_response.json()


def test_idempotency_key_is_scoped_to_tenant():
    key = "stage3-test-003"

    first_response = client.post(
        "/generate",
        headers={
            "X-Tenant-Key": "tenant-001",
            "Idempotency-Key": key,
        },
        json={
            "input_tokens": 100,
            "output_tokens": 50,
        },
    )

    second_response = client.post(
        "/generate",
        headers={
            "X-Tenant-Key": "tenant-002",
            "Idempotency-Key": key,
        },
        json={
            "input_tokens": 200,
            "output_tokens": 100,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert first_response.json()["tenant_key"] == "tenant-001"
    assert second_response.json()["tenant_key"] == "tenant-002"

    assert (
        first_response.json()["usage_event_id"]
        != second_response.json()["usage_event_id"]
    )


def test_missing_idempotency_key():
    response = client.post(
        "/generate",
        headers={
            "X-Tenant-Key": "tenant-001",
        },
        json={
            "input_tokens": 100,
            "output_tokens": 50,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Idempotency-Key header is required."


def test_invalid_token_breakdown():
    response = client.post(
        "/generate",
        headers={
            "X-Tenant-Key": "tenant-001",
            "Idempotency-Key": "stage3-test-004",
        },
        json={
            "input_tokens": 100,
            "cached_input_tokens": 200,
            "output_tokens": 50,
        },
    )

    assert response.status_code == 422