from app.db import get_connection


def is_event_processed(stripe_event_id: str) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM stripe_events
                WHERE stripe_event_id = %s;
                """,
                (stripe_event_id,),
            )

            return cursor.fetchone() is not None


def record_event(
    stripe_event_id: str,
    event_type: str,
) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO stripe_events (
                    stripe_event_id,
                    event_type
                )
                VALUES (%s, %s)
                ON CONFLICT (stripe_event_id)
                DO NOTHING;
                """,
                (stripe_event_id, event_type),
            )