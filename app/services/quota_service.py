from fastapi import HTTPException, status

from app.repositories.quota_repository import get_current_ai_token_usage


def check_ai_token_quota(
    tenant_id: str,
    requested_tokens: int,
    ai_token_limit: int,
) -> None:
    current_usage = get_current_ai_token_usage(tenant_id)

    if current_usage + requested_tokens > ai_token_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI token quota exceeded.",
        )