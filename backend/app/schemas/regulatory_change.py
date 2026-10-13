from pydantic import BaseModel, ConfigDict


class RegulatoryChangeResponse(BaseModel):
    id: int
    regulatory_change_id: str
    regulatory_act: str
    change_topic: str
    change_description: str
    synthetic: bool

    model_config = ConfigDict(
        from_attributes=True
    )