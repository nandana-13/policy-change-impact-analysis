from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PolicyVersionCreate(BaseModel):
    policy_version_id: str
    version_number: int
    effective_date: date
    change_description: str
    status: str = "revised"
    synthetic: bool = True


class PolicyVersionResponse(BaseModel):
    id: int
    policy_version_id: str
    policy_id: str
    version_number: int
    effective_date: date
    change_description: str
    status: str
    synthetic: bool

    model_config = ConfigDict(
        from_attributes=True
    )