from dataclasses import dataclass
from typing import Any


@dataclass
class BillingJob:
    job_id: str
    tenant_id: str
    job_type: str
    payload: dict[str, Any]