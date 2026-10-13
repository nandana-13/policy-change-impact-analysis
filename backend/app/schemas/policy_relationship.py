from pydantic import BaseModel, ConfigDict


class PolicyRelationshipCreate(BaseModel):
    relationship_id: str
    target_policy_id: str
    relationship_type: str
    synthetic: bool = True


class PolicyRelationshipResponse(BaseModel):
    id: int
    relationship_id: str
    source_policy_id: str
    target_policy_id: str
    relationship_type: str
    synthetic: bool

    model_config = ConfigDict(
        from_attributes=True
    )