import stripe
from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings
from app.repositories.stripe_event_repository import (
    is_event_processed,
    record_event,
)
from app.services.subscription_service import (
    handle_checkout_completed,
    handle_subscription_deleted,
    handle_subscription_updated,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None),
) -> dict:
    payload = await request.body()

    if not stripe_signature:
        raise HTTPException(
            status_code=400,
            detail="Stripe-Signature header is required.",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe webhook.",
        )

    event_id = event["id"]
    event_type = event["type"]

    if is_event_processed(event_id):
        return {
            "received": True,
            "duplicate": True,
            "event_id": event_id,
        }

    event_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        handle_checkout_completed(event_object)

    elif event_type == "customer.subscription.updated":
        handle_subscription_updated(event_object)

    elif event_type == "customer.subscription.deleted":
        handle_subscription_deleted(event_object)

    else:
        return {
            "received": True,
            "ignored": True,
            "event_id": event_id,
            "event_type": event_type,
        }

    record_event(
        stripe_event_id=event_id,
        event_type=event_type,
    )

    return {
        "received": True,
        "event_id": event_id,
        "event_type": event_type,
    }