from typing import Any

from app.repositories.subscription_repository import (
    get_tenant_by_stripe_subscription_id,
    update_subscription_from_stripe,
)


def _stripe_timestamp(value: Any) -> Any | None:
    if value is None:
        return None

    from datetime import datetime, timezone

    return datetime.fromtimestamp(value, tz=timezone.utc)


def handle_checkout_completed(session: Any) -> None:
    session = session.to_dict()

    metadata = session.get("metadata") or {}
    tenant_id = metadata.get("tenant_id")

    if not tenant_id:
        raise ValueError("Checkout session is missing tenant_id metadata.")

    stripe_customer_id = session.get("customer")
    stripe_subscription_id = session.get("subscription")

    if not stripe_subscription_id:
        raise ValueError("Checkout session is missing subscription ID.")

    update_subscription_from_stripe(
        tenant_id=tenant_id,
        plan_code="pro",
        status="active",
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
    )


def handle_subscription_updated(subscription: Any) -> None:
    subscription = subscription.to_dict()

    stripe_subscription_id = subscription.get("id")

    if not stripe_subscription_id:
        raise ValueError("Stripe subscription is missing ID.")

    tenant = get_tenant_by_stripe_subscription_id(
        stripe_subscription_id
    )

    if tenant is None:
        raise ValueError(
            f"No tenant found for Stripe subscription: "
            f"{stripe_subscription_id}"
        )

    stripe_status = subscription.get("status")

    allowed_statuses = {
        "active": "active",
        "trialing": "trialing",
        "past_due": "past_due",
        "canceled": "canceled",
    }

    status = allowed_statuses.get(stripe_status)

    if status is None:
        raise ValueError(
            f"Unsupported Stripe subscription status: {stripe_status}"
        )

    items = subscription.get("items") or {}
    items_data = items.get("data") or []

    current_period_start = None
    current_period_end = None

    if items_data:
        current_period_start = items_data[0].get("current_period_start")
        current_period_end = items_data[0].get("current_period_end")

    update_subscription_from_stripe(
        tenant_id=tenant["tenant_id"],
        plan_code="pro",
        status=status,
        stripe_customer_id=subscription.get("customer"),
        stripe_subscription_id=stripe_subscription_id,
        current_period_start=_stripe_timestamp(current_period_start),
        current_period_end=_stripe_timestamp(current_period_end),
    )


def handle_subscription_deleted(subscription: Any) -> None:
    subscription = subscription.to_dict()

    stripe_subscription_id = subscription.get("id")

    if not stripe_subscription_id:
        raise ValueError("Stripe subscription is missing ID.")

    tenant = get_tenant_by_stripe_subscription_id(
        stripe_subscription_id
    )

    if tenant is None:
        raise ValueError(
            f"No tenant found for Stripe subscription: "
            f"{stripe_subscription_id}"
        )

    update_subscription_from_stripe(
        tenant_id=tenant["tenant_id"],
        plan_code="free",
        status="canceled",
        stripe_customer_id=subscription.get("customer"),
        stripe_subscription_id=stripe_subscription_id,
        current_period_start=_stripe_timestamp(
            subscription.get("current_period_start")
        ),
        current_period_end=_stripe_timestamp(
            subscription.get("current_period_end")
        ),
    )