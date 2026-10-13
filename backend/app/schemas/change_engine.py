from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ChangeItem(BaseModel):
    section: str
    old_section: Optional[str] = None
    new_section: Optional[str] = None

    change_type: str

    similarity: float

    old_text: Optional[str] = None
    new_text: Optional[str] = None


class ChangeSummary(BaseModel):
    total_sections: int

    added: int
    removed: int
    modified: int
    unchanged: int

    changed_sections: int
    change_percentage: float


class VersionComparisonMetadata(BaseModel):
    version_number: int
    policy_version_id: str

    effective_date: Optional[date] = None
    status: Optional[str] = None

    document_id: str
    file_name: str


class PolicyComparisonInfo(BaseModel):
    policy_id: str
    policy_name: Optional[str] = None


class ChangeComparisonResponse(BaseModel):
    policy: PolicyComparisonInfo

    comparison: dict

    summary: ChangeSummary

    changes: List[ChangeItem]

    model_config = ConfigDict(
        from_attributes=True
    )