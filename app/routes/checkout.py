from fastapi import APIRouter, Depends

from app.dependencies import get_current_tenant
from app.services.stripe_service import create_checkout_session


router = APIRouter(
    prefix="/checkout",
    tags=["checkout"],
)


@router.post("/pro")
def checkout_pro(
    tenant: dict = Depends(get_current_tenant),
) -> dict:
    session = create_checkout_session(
        tenant_id=tenant["id"],
    )

    return {
        "checkout_url": session.url,
        "session_id": session.id,
    }