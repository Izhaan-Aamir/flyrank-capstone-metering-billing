from app.routes.webhooks import router as webhook_router
from fastapi import FastAPI
from app.routes.checkout import router as checkout_router
from app.routes.tenants import router as tenants_router
from app.routes.usage import router as usage_router


app = FastAPI(
    title="Usage Metering & Billing Engine",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(tenants_router)
app.include_router(usage_router)
app.include_router(checkout_router)
app.include_router(webhook_router)