from typing import Any

from app.db import get_connection


def get_plan_id_by_code(plan_code: str) -> str | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM plans
                WHERE code = %s;
                """,
                (plan_code,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return str(row[0])


def get_tenant_by_stripe_subscription_id(
    stripe_subscription_id: str,
) -> dict[str, Any] | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    tenant_id,
                    stripe_customer_id,
                    stripe_subscription_id,
                    status
                FROM subscriptions
                WHERE stripe_subscription_id = %s;
                """,
                (stripe_subscription_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "tenant_id": str(row[0]),
                "stripe_customer_id": row[1],
                "stripe_subscription_id": row[2],
                "status": row[3],
            }


def update_subscription_from_stripe(
    tenant_id: str,
    plan_code: str,
    status: str,
    stripe_customer_id: str | None,
    stripe_subscription_id: str | None,
    current_period_start: Any | None = None,
    current_period_end: Any | None = None,
) -> None:
    plan_id = get_plan_id_by_code(plan_code)

    if plan_id is None:
        raise ValueError(f"Plan not found: {plan_code}")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE subscriptions
                SET
                    plan_id = %s,
                    status = %s,
                    stripe_customer_id = %s,
                    stripe_subscription_id = %s,
                    current_period_start = %s,
                    current_period_end = %s,
                    updated_at = NOW()
                WHERE tenant_id = %s;
                """,
                (
                    plan_id,
                    status,
                    stripe_customer_id,
                    stripe_subscription_id,
                    current_period_start,
                    current_period_end,
                    tenant_id,
                ),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    f"Subscription not found for tenant: {tenant_id}"
                )