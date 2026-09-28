from app.repositories.stripe_event_repository import record_event
from fastapi.testclient import TestClient
import uuid
from app.main import app


client = TestClient(app)


def test_stripe_webhook_rejects_invalid_signature():
    response = client.post(
        "/webhooks/stripe",
        headers={
            "Stripe-Signature": "invalid-signature",
        },
        content=b'{"id":"evt_invalid","type":"checkout.session.completed"}',
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Stripe webhook."

def test_stripe_webhook_requires_signature():
    response = client.post(
        "/webhooks/stripe",
        content=b'{"id":"evt_missing_signature","type":"checkout.session.completed"}',
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Stripe-Signature header is required."

def test_duplicate_stripe_event_is_ignored(monkeypatch):
    import app.routes.webhooks as webhooks

    event_id = "evt_test_duplicate_001"

    record_event(
        stripe_event_id=event_id,
        event_type="checkout.session.completed",
    )

    fake_event = {
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {
            "object": {},
        },
    }

    monkeypatch.setattr(
        webhooks.stripe.Webhook,
        "construct_event",
        lambda payload, signature, secret: fake_event,
    )

    response = client.post(
        "/webhooks/stripe",
        headers={"Stripe-Signature": "valid-for-test"},
        content=b"{}",
    )

    assert response.status_code == 200
    assert response.json() == {
        "received": True,
        "duplicate": True,
        "event_id": event_id,
    }

def test_valid_checkout_event_is_dispatched(monkeypatch):
    import app.routes.webhooks as webhooks

    fake_event = {
        "id": f"evt_test_checkout_dispatch_{uuid.uuid4()}",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_001",
            },
        },
    }

    called = {"value": False}

    def fake_handler(event_object):
        called["value"] = True
        assert event_object == {"id": "cs_test_001"}

    monkeypatch.setattr(
        webhooks.stripe.Webhook,
        "construct_event",
        lambda payload, signature, secret: fake_event,
    )

    monkeypatch.setattr(
        webhooks,
        "handle_checkout_completed",
        fake_handler,
    )

    response = client.post(
        "/webhooks/stripe",
        headers={"Stripe-Signature": "valid-for-test"},
        content=b"{}",
    )

    assert response.status_code == 200
    assert called["value"] is True
    assert response.json()["event_id"] == fake_event["id"]