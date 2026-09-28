import argparse

import psycopg


FREE_PLAN = {
    "code": "free",
    "name": "Free",
    "api_call_limit": 1_000,
    "ai_token_limit": 100_000,
}

PRO_PLAN = {
    "code": "pro",
    "name": "Pro",
    "api_call_limit": 10_000,
    "ai_token_limit": 1_000_000,
}

TENANTS = [
    ("tenant-001", "Demo Tenant One"),
    ("tenant-002", "Demo Tenant Two"),
]


def seed_database(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            for plan in (FREE_PLAN, PRO_PLAN):
                cursor.execute(
                    """
                    INSERT INTO plans (
                        code,
                        name,
                        api_call_limit,
                        ai_token_limit
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (code)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        api_call_limit = EXCLUDED.api_call_limit,
                        ai_token_limit = EXCLUDED.ai_token_limit,
                        active = TRUE
                    RETURNING id;
                    """,
                    (
                        plan["code"],
                        plan["name"],
                        plan["api_call_limit"],
                        plan["ai_token_limit"],
                    ),
                )

            cursor.execute(
                "SELECT id FROM plans WHERE code = %s;",
                ("free",),
            )
            free_plan_id = cursor.fetchone()[0]

            for tenant_key, tenant_name in TENANTS:
                cursor.execute(
                    """
                    INSERT INTO tenants (tenant_key, name)
                    VALUES (%s, %s)
                    ON CONFLICT (tenant_key)
                    DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                    """,
                    (tenant_key, tenant_name),
                )

                tenant_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO subscriptions (
                        tenant_id,
                        plan_id,
                        status
                    )
                    VALUES (%s, %s, 'active')
                    ON CONFLICT (tenant_id)
                    DO UPDATE SET
                        plan_id = EXCLUDED.plan_id,
                        status = 'active',
                        updated_at = NOW();
                    """,
                    (tenant_id, free_plan_id),
                )

    print("Database seed completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the Usage Metering & Billing Engine database."
    )
    parser.add_argument(
        "--database-url",
        required=True,
        help="PostgreSQL connection URL.",
    )

    args = parser.parse_args()
    seed_database(args.database_url)


if __name__ == "__main__":
    main()