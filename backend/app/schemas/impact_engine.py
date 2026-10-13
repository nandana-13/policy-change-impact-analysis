
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


class LegalEvidenceResponse(BaseModel):
    chunk_id: Optional[str] = None
    act_title: Optional[str] = None
    document: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[str] = None
    category: Optional[str] = None
    content_type: Optional[str] = None

    similarity: float = 0.0
    evidence: str = ""

    source: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    act_uri: Optional[str] = None

    jurisdiction: Optional[str] = None
    chunk_index: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True
    )

    @model_validator(mode="before")
    @classmethod
    def populate_evidence(cls, data: Any) -> Any:
        """
        Map legal text from the retrieval pipeline into the
        API response's evidence field.

        LegalRetrievalService may return evidence_text, while
        the Impact Engine may normalize the text as content.
        """
        if isinstance(data, dict):
            evidence = data.get("evidence")

            if not evidence:
                evidence = (
                    data.get("evidence_text")
                    or data.get("content")
                    or data.get("text")
                    or data.get("document_text")
                    or data.get("document")
                    or ""
                )

                data = dict(data)
                data["evidence"] = evidence

        return data


class PolicyEvidenceResponse(BaseModel):
    chunk_id: Optional[str] = None

    policy_id: Optional[str] = None
    policy_name: Optional[str] = None

    version_number: Optional[int] = None
    policy_version_id: Optional[str] = None

    effective_date: Optional[str] = None
    status: Optional[str] = None

    section_index: Optional[int] = None
    section_title: Optional[str] = None

    similarity: float = 0.0
    evidence: str = ""

    file_path: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


class RelationshipResponse(BaseModel):
    relationship_id: Optional[str] = None

    source_policy_id: Optional[str] = None
    target_policy_id: Optional[str] = None

    relationship_type: Optional[str] = None

    relationship_depth: Optional[int] = None

    direction: Optional[str] = None
    related_policy_id: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


class ImpactItemResponse(BaseModel):
    policy_id: str

    policy_name: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None

    version_number: Optional[int] = None
    policy_version_id: Optional[str] = None

    effective_date: Optional[str] = None
    status: Optional[str] = None

    impact_score: float = 0.0

    impact_classification: str
    impact_type: str
    expected_action: str

    reason: str

    policy_evidence: List[
        PolicyEvidenceResponse
    ] = []

    relationships: List[
        RelationshipResponse
    ] = []

    model_config = ConfigDict(
        from_attributes=True
    )


class ImpactAnalysisResponse(BaseModel):
    regulatory_change_id: str
    regulatory_act: str
    change_topic: str
    change_description: str

    candidate_count: int
    direct_impact_count: int
    indirect_impact_count: int
    no_impact_count: int

    total_analysed: int = 0

    legal_evidence: List[
        LegalEvidenceResponse
    ] = []

    impact_items: List[
        ImpactItemResponse
    ] = []

    model_config = ConfigDict(
        from_attributes=True
    )
