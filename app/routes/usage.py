from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.services.quota_service import check_ai_token_quota
from app.dependencies import get_current_tenant
from app.repositories.usage_repository import create_usage_event
from app.schemas.usage import GenerateRequest, UsageResponse


router = APIRouter(
    tags=["usage"],
)


@router.post("/generate", response_model=UsageResponse)
def generate(
    request: GenerateRequest,
    tenant: dict = Depends(get_current_tenant),
    idempotency_key: str | None = Header(default=None),
) -> dict:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required.",
        )

    if len(idempotency_key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must be 255 characters or fewer.",
        )

    check_ai_token_quota(
        tenant_id=tenant["id"],
        requested_tokens=(
            request.input_tokens
            + request.output_tokens
            + request.reasoning_tokens
        ),
        ai_token_limit=tenant["ai_token_limit"],
    )

    usage_event = create_usage_event(
        tenant_id=tenant["id"],
        idempotency_key=idempotency_key,
        input_tokens=request.input_tokens,
        cached_input_tokens=request.cached_input_tokens,
        output_tokens=request.output_tokens,
        reasoning_tokens=request.reasoning_tokens,
    )

    return {
        "usage_event_id": usage_event["usage_event_id"],
        "tenant_key": tenant["tenant_key"],
        "usage_type": usage_event["usage_type"],
        "quantity": usage_event["quantity"],
        "input_tokens": usage_event["input_tokens"],
        "cached_input_tokens": usage_event["cached_input_tokens"],
        "output_tokens": usage_event["output_tokens"],
        "reasoning_tokens": usage_event["reasoning_tokens"],
    }