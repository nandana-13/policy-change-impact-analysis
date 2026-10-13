from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ================================================================
# PHASE 2F.1
# ================================================================

class CandidatePolicyResponse(BaseModel):
    policy_id: str
    policy_name: str
    category: str
    department: str

    version_number: Optional[int] = None
    policy_version_id: Optional[str] = None
    effective_date: Optional[str] = None
    status: Optional[str] = None

    relevance_score: float
    semantic_score: float
    lexical_score: float
    term_overlap_score: float
    section_score: float
    subject_score: float

    # Topic-aware retrieval scores
    retrieval_score: float = 0.0
    topic_score: float = 0.0
    topic_evidence_score: float = 0.0
    generic_evidence_score: float = 0.0
    section_specificity_score: float = 0.0

    matched_section: Optional[str] = None
    evidence: str

    model_config = ConfigDict(from_attributes=True)


class RegulatoryCandidateResponse(BaseModel):
    regulatory_change_id: str
    regulatory_act: str
    change_topic: str
    change_description: str

    topic_terms: List[str] = Field(default_factory=list)

    candidate_count: int
    candidates: List[CandidatePolicyResponse]


# ================================================================
# PHASE 2F.2 - LEGAL EVIDENCE
# ================================================================

class LegalEvidenceResponse(BaseModel):
    chunk_id: Optional[str] = None
    act_title: Optional[str] = None
    document: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[str] = None

    similarity: float = 0.0

    evidence: str


# ================================================================
# PHASE 2F.2 - COMPANY POLICY EVIDENCE
# ================================================================

class PolicyEvidenceResponse(BaseModel):
    section: Optional[str] = None

    version_number: Optional[int] = None
    policy_version_id: Optional[str] = None

    similarity: float = 0.0

    evidence: str


# ================================================================
# PHASE 2F.2 - RELATIONSHIP
# ================================================================

class RelationshipContextResponse(BaseModel):
    relationship_id: Optional[str] = None

    via_policy_id: str

    relationship_type: str


# ================================================================
# PHASE 2F.2 - IMPACT ITEM
# ================================================================

class ImpactItemResponse(BaseModel):
    policy_id: str

    policy_name: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None

    version_number: Optional[int] = None
    policy_version_id: Optional[str] = None
    effective_date: Optional[str] = None
    status: Optional[str] = None

    # direct / indirect / no_impact
    impact_status: str

    impact_confidence: float = 0.0

    # process / documentation / recordkeeping / compliance / none
    impact_type: str

    # review_required / monitor / no_change_expected
    expected_action: str

    relevance_score: float = 0.0
    topic_score: float = 0.0
    topic_evidence_score: float = 0.0

    matched_section: Optional[str] = None

    policy_evidence: List[PolicyEvidenceResponse] = Field(
        default_factory=list
    )

    retrieved_policy_evidence: str = ""

    relationship_context: List[RelationshipContextResponse] = Field(
        default_factory=list
    )

    reason: str


# ================================================================
# PHASE 2F.2 - COMPLETE RESPONSE
# ================================================================

class ImpactAnalysisResponse(BaseModel):
    regulatory_change_id: str

    regulatory_act: str

    change_topic: str

    change_description: str

    legal_evidence: List[LegalEvidenceResponse] = Field(
        default_factory=list
    )

    candidate_count: int

    direct_impact_count: int

    indirect_impact_count: int

    impact_count: int

    impacts: List[ImpactItemResponse]