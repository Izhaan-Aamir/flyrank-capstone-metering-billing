from typing import Any

from app.db import get_connection


def create_usage_event(
    tenant_id: str,
    idempotency_key: str,
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
) -> dict[str, Any]:
    quantity = input_tokens + output_tokens + reasoning_tokens

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usage_events (
                    tenant_id,
                    usage_type,
                    quantity,
                    idempotency_key,
                    input_tokens,
                    cached_input_tokens,
                    output_tokens,
                    reasoning_tokens
                )
                VALUES (
                    %s,
                    'ai_tokens',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (tenant_id, idempotency_key)
                DO NOTHING
                RETURNING
                    id,
                    tenant_id,
                    usage_type,
                    quantity,
                    idempotency_key,
                    input_tokens,
                    cached_input_tokens,
                    output_tokens,
                    reasoning_tokens;
                """,
                (
                    tenant_id,
                    quantity,
                    idempotency_key,
                    input_tokens,
                    cached_input_tokens,
                    output_tokens,
                    reasoning_tokens,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                cursor.execute(
                    """
                    SELECT
                        id,
                        tenant_id,
                        usage_type,
                        quantity,
                        idempotency_key,
                        input_tokens,
                        cached_input_tokens,
                        output_tokens,
                        reasoning_tokens
                    FROM usage_events
                    WHERE tenant_id = %s
                      AND idempotency_key = %s;
                    """,
                    (tenant_id, idempotency_key),
                )

                row = cursor.fetchone()

            return {
                "usage_event_id": str(row[0]),
                "tenant_id": str(row[1]),
                "usage_type": row[2],
                "quantity": row[3],
                "idempotency_key": row[4],
                "input_tokens": row[5],
                "cached_input_tokens": row[6],
                "output_tokens": row[7],
                "reasoning_tokens": row[8],
            }