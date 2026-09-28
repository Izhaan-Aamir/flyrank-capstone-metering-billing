from fastapi import Header, HTTPException, status

from app.repositories.tenant_repository import get_tenant_by_key


def get_current_tenant(
    x_tenant_key: str | None = Header(default=None),
) -> dict:
    if not x_tenant_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Key header is required.",
        )

    tenant = get_tenant_by_key(x_tenant_key)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    return tenant