from pydantic import BaseModel, ConfigDict
from typing import Optional


class PolicyBase(BaseModel):
    policy_name: str
    category: str
    department: str
    description: str
    synthetic: bool = True


class PolicyCreate(PolicyBase):
    policy_id: str


class PolicyUpdate(BaseModel):
    policy_name: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    synthetic: Optional[bool] = None


class PolicyResponse(PolicyBase):
    id: int
    policy_id: str

    model_config = ConfigDict(
        from_attributes=True
    )