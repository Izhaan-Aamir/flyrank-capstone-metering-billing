from typing import Any

from app.db import get_connection


def get_tenant_by_key(tenant_key: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    t.id,
                    t.tenant_key,
                    t.name,
                    s.status,
                    p.code AS plan_code,
                    p.name AS plan_name,
                    p.api_call_limit,
                    p.ai_token_limit
                FROM tenants AS t
                JOIN subscriptions AS s
                    ON s.tenant_id = t.id
                JOIN plans AS p
                    ON p.id = s.plan_id
                WHERE t.tenant_key = %s;
                """,
                (tenant_key,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "id": str(row[0]),
                "tenant_key": row[1],
                "name": row[2],
                "status": row[3],
                "plan_code": row[4],
                "plan_name": row[5],
                "api_call_limit": row[6],
                "ai_token_limit": row[7],
            }