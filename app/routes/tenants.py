from fastapi import APIRouter, Depends

from app.dependencies import get_current_tenant
from app.schemas.tenant import TenantResponse


router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
)


@router.get("/me", response_model=TenantResponse)
def get_my_tenant(
    tenant: dict = Depends(get_current_tenant),
) -> dict:
    return tenant