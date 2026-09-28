from fastapi import FastAPI

from app.routes.tenants import router as tenants_router


app = FastAPI(
    title="Usage Metering & Billing Engine",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(tenants_router)