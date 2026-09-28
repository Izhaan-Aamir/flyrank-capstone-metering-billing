import stripe

from app.config import settings


stripe.api_key = settings.stripe_secret_key


def create_checkout_session(
    tenant_id: str,
    customer_email: str | None = None,
):
    return stripe.checkout.Session.create(
        mode="subscription",
        line_items=[
            {
                "price": settings.stripe_pro_price_id,
                "quantity": 1,
            }
        ],
        metadata={"tenant_id": tenant_id},
        subscription_data={
            "metadata": {
                "tenant_id": tenant_id,
            },
        },
        customer_email=customer_email,
        success_url="http://127.0.0.1:8000/checkout/success",
        cancel_url="http://127.0.0.1:8000/checkout/cancel",
    )