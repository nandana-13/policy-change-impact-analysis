from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PolicyDocumentResponse(BaseModel):
    document_id: str
    policy_id: str
    policy_version_id: str
    version_number: int
    file_name: str
    content_type: str
    file_size: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)