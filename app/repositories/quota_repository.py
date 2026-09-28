from typing import Any

from app.db import get_connection


def get_current_ai_token_usage(
    tenant_id: str,
) -> int:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(quantity), 0)
                FROM usage_events
                WHERE tenant_id = %s
                  AND usage_type = 'ai_tokens'
                  AND occurred_at >= date_trunc('month', CURRENT_TIMESTAMP);
                """,
                (tenant_id,),
            )

            row = cursor.fetchone()

            return int(row[0])