from pydantic import BaseModel


class TenantResponse(BaseModel):
    id: str
    tenant_key: str
    name: str
    status: str
    plan_code: str
    plan_name: str
    api_call_limit: int
    ai_token_limit: int