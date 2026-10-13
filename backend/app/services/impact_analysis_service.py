from typing import Any, Dict, List, Optional, Set

import re

from sqlalchemy.orm import Session

from app.models.regulatory_change import RegulatoryChange
from app.models.policy import Policy
from app.models.policy_version import PolicyVersion
from app.models.policy_relationship import PolicyRelationship

from app.services.policy_retrieval_service import (
    get_policy_retrieval_service,
)


class ImpactAnalysisService:

    """
    PolicyLens

    Phase 2F.1 + Phase 2F.2

    ------------------------------------------------------------

    Phase 2F.1

        Regulatory Change
                |
                v
        Topic Expansion
                |
                v
        Company Policy Retrieval
                |
                v
        Topic-aware Scoring
                |
                v
        Candidate Policies


    Phase 2F.2

        Candidate Policies
                |
                v
        Direct Impact Detection
                |
                v
        Policy Relationships
                |
                v
        Indirect Impact Detection
                |
                v
        Impact Type
                |
                v
        Expected Action
                |
                v
        Legal Evidence
                +
        Company Policy Evidence
                |
                v
        Explainable Impact Result

    ------------------------------------------------------------

    IMPORTANT:

    Ground-truth data is NOT used during runtime inference.

    It can be used later for evaluation.
    """

    # ============================================================
    # TOPIC VOCABULARY
    # ============================================================

    TOPIC_EXPANSIONS = {

        "retention": {
            "retention",
            "retained",
            "retain",
            "retention period",
            "retention periods",
            "storage",
            "stored",
            "archive",
            "archival",
            "disposal",
            "dispose",
            "disposed",
            "deletion",
            "delete",
            "deleted",
            "destruction",
            "destroy",
            "destroyed",
            "secure deletion",
            "data lifecycle",
            "legal hold",
            "record lifecycle",
        },

        "disposal": {
            "disposal",
            "dispose",
            "disposed",
            "deletion",
            "delete",
            "deleted",
            "destruction",
            "destroy",
            "destroyed",
            "secure deletion",
            "anonymisation",
            "anonymization",
            "archive",
            "archival",
        },

        "privacy": {
            "privacy",
            "personal data",
            "personal information",
            "data subject",
            "processing",
            "lawful basis",
            "consent",
            "privacy notice",
            "data protection",
        },

        "personal_data": {
            "personal data",
            "personal information",
            "employee data",
            "customer data",
            "data subject",
            "processing",
            "privacy",
            "confidential",
            "data protection",
        },

        "data_protection": {
            "data protection",
            "personal data",
            "personal information",
            "privacy",
            "data subject",
            "processing",
            "controller",
            "processor",
            "security",
        },

        "incident": {
            "incident",
            "data incident",
            "security incident",
            "breach",
            "data breach",
            "notification",
            "reporting",
            "containment",
            "response",
            "investigation",
        },

        "breach": {
            "breach",
            "data breach",
            "security incident",
            "incident response",
            "notification",
            "notify",
            "investigation",
            "containment",
        },

        "equality": {
            "equality",
            "equal opportunity",
            "discrimination",
            "protected characteristic",
            "fair treatment",
            "employment decision",
            "recruitment",
        },

        "employment": {
            "employment",
            "employee",
            "recruitment",
            "selection",
            "employment decision",
            "workplace",
            "worker",
            "staff",
        },

        "accommodation": {
            "accommodation",
            "workplace adjustment",
            "reasonable adjustment",
            "disability",
            "accessibility",
            "adjustment",
        },

        "grievance": {
            "grievance",
            "complaint",
            "employee complaint",
            "investigation",
            "disciplinary",
            "escalation",
            "resolution",
        },

        "financial_reporting": {
            "financial reporting",
            "financial statement",
            "reporting",
            "accounting",
            "financial records",
            "disclosure",
            "reporting controls",
        },

        "audit": {
            "audit",
            "auditor",
            "audit evidence",
            "audit trail",
            "assurance",
            "financial audit",
            "internal audit",
        },

        "tax": {
            "tax",
            "taxation",
            "tax records",
            "tax reporting",
            "tax compliance",
            "taxable",
            "tax authority",
        },

        "payroll": {
            "payroll",
            "salary",
            "wages",
            "employee compensation",
            "pay",
            "earnings",
            "payroll records",
        },

        "procurement": {
            "procurement",
            "supplier",
            "supplier selection",
            "purchasing",
            "vendor",
            "contractor",
            "tender",
        },

        "planning": {
            "planning",
            "planning permission",
            "development",
            "property",
            "land",
            "planning authority",
            "development approval",
        },

        "community": {
            "community",
            "community engagement",
            "local community",
            "stakeholder",
            "consultation",
            "public consultation",
        },
    }

    # ============================================================
    # GENERIC VOCABULARY
    # ============================================================

    GENERIC_TERMS = {
        "policy",
        "policies",
        "review",
        "reviews",
        "reviewed",
        "regulatory",
        "regulation",
        "regulations",
        "requirement",
        "requirements",
        "evidence",
        "record",
        "records",
        "control",
        "controls",
        "management",
        "monitoring",
        "monitor",
        "change",
        "changes",
        "compliance",
        "compliant",
        "organization",
        "organisational",
        "organizational",
        "procedure",
        "procedures",
        "process",
        "processes",
        "document",
        "documentation",
        "responsibility",
        "responsibilities",
        "reporting",
        "report",
        "reports",
    }

    STOPWORDS = {
        "and",
        "or",
        "the",
        "of",
        "to",
        "for",
        "in",
        "on",
        "a",
        "an",
        "with",
        "from",
        "by",
        "is",
        "are",
        "was",
        "were",
        "this",
        "that",
        "as",
        "at",
        "be",
        "it",
        "its",
        "into",
        "through",
        "during",
        "within",
        "involving",
        "scenario",
        "synthetic",
    }

    GENERIC_SECTIONS = {
        "monitoring and review",
        "records and evidence",
        "roles and responsibilities",
        "purpose",
        "scope",
        "definitions",
        "document control",
        "exceptions and escalation",
        "related policies and controls",
        "version change summary",
    }

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        self.policy_retrieval = (
            get_policy_retrieval_service()
        )

    # ============================================================
    # REGULATORY CHANGE
    # ============================================================

    def get_regulatory_change(
        self,
        db: Session,
        regulatory_change_id: str,
    ) -> Optional[RegulatoryChange]:

        return (
            db.query(RegulatoryChange)
            .filter(
                RegulatoryChange.regulatory_change_id
                == regulatory_change_id
            )
            .first()
        )

    # ============================================================
    # TEXT NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_text(value: Any) -> str:

        if value is None:
            return ""

        text = str(value).lower()

        text = text.replace("_", " ")
        text = text.replace("-", " ")

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @classmethod
    def _tokenize(
        cls,
        value: Any,
    ) -> Set[str]:

        text = cls._normalize_text(value)

        if not text:
            return set()

        tokens = set(
            text.split()
        )

        return {
            token
            for token in tokens
            if token not in cls.GENERIC_TERMS
            and token not in cls.STOPWORDS
            and len(token) > 2
        }

    # ============================================================
    # TOPIC EXPANSION
    # ============================================================

    def _expand_topic(
        self,
        regulatory_change: RegulatoryChange,
    ) -> List[str]:

        topic = self._normalize_text(
            regulatory_change.change_topic
        )

        description = self._normalize_text(
            regulatory_change.change_description
        )

        topic_terms: Set[str] = set()

        topic_tokens = set(
            topic.split()
        )

        for token in topic_tokens:

            if (
                token not in self.GENERIC_TERMS
                and token not in self.STOPWORDS
            ):
                topic_terms.add(token)

        for key, expansion_terms in (
            self.TOPIC_EXPANSIONS.items()
        ):

            normalized_key = self._normalize_text(
                key
            )

            key_tokens = set(
                normalized_key.split()
            )

            if (
                normalized_key in topic
                or normalized_key.replace(
                    " ",
                    "_",
                )
                in str(
                    regulatory_change.change_topic
                ).lower()
                or key_tokens.intersection(
                    topic_tokens
                )
            ):

                topic_terms.update(
                    expansion_terms
                )

        description_tokens = self._tokenize(
            description
        )

        topic_terms.update(
            description_tokens
        )

        topic_terms = {
            term
            for term in topic_terms
            if term
            and term not in self.GENERIC_TERMS
            and term not in self.STOPWORDS
            and len(term) > 2
        }

        return sorted(
            topic_terms,
            key=lambda value: (
                -len(value),
                value,
            ),
        )

    # ============================================================
    # QUERY CONSTRUCTION
    # ============================================================

    def build_policy_query(
        self,
        regulatory_change: RegulatoryChange,
    ) -> str:

        topic_terms = self._expand_topic(
            regulatory_change
        )

        parts: List[str] = []

        if regulatory_change.regulatory_act:
            parts.append(
                "Regulatory Act: "
                + str(
                    regulatory_change.regulatory_act
                )
            )

        if regulatory_change.change_topic:
            parts.append(
                "Change Topic: "
                + str(
                    regulatory_change.change_topic
                )
            )

        if regulatory_change.change_description:
            parts.append(
                "Change Description: "
                + str(
                    regulatory_change.change_description
                )
            )

        if topic_terms:
            parts.append(
                "Relevant Regulatory Concepts: "
                + ", ".join(topic_terms)
            )

        return "\n".join(parts)

    def build_focused_policy_query(
        self,
        regulatory_change: RegulatoryChange,
    ) -> str:

        topic_terms = self._expand_topic(
            regulatory_change
        )

        focused_terms = topic_terms[:25]

        topic = (
            regulatory_change.change_topic
            or ""
        )

        return (
            f"Policy topic: {topic}\n"
            "Topic-specific requirements: "
            + ", ".join(focused_terms)
        )

    # ============================================================
    # CANDIDATE POLICY RETRIEVAL
    # ============================================================

    def retrieve_candidate_policies(
        self,
        regulatory_change: RegulatoryChange,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:

        retrieval_pool = max(
            50,
            top_k * 5,
        )

        primary_query = (
            self.build_policy_query(
                regulatory_change
            )
        )

        focused_query = (
            self.build_focused_policy_query(
                regulatory_change
            )
        )

        primary_results = (
            self.policy_retrieval.retrieve(
                query=primary_query,
                top_k=retrieval_pool,
                status="active",
            )
        )

        focused_results = (
            self.policy_retrieval.retrieve(
                query=focused_query,
                top_k=retrieval_pool,
                status="active",
            )
        )

        merged = []

        for result in (
            primary_results or []
        ):

            item = dict(result)

            item["_retrieval_source"] = (
                "primary"
            )

            merged.append(item)

        for result in (
            focused_results or []
        ):

            item = dict(result)

            item["_retrieval_source"] = (
                "focused"
            )

            merged.append(item)

        return merged

    # ============================================================
    # METADATA EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_metadata(
        result: Dict[str, Any],
    ) -> Dict[str, Any]:

        metadata = result.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        aliases = {

            "policy_id": [
                "policy_id",
                "policyId",
            ],

            "policy_name": [
                "policy_name",
                "policyName",
                "name",
            ],

            "category": [
                "category",
                "policy_category",
            ],

            "department": [
                "department",
                "policy_department",
            ],

            "version_number": [
                "version_number",
                "version",
            ],

            "policy_version_id": [
                "policy_version_id",
                "policyVersionId",
            ],

            "effective_date": [
                "effective_date",
                "effectiveDate",
            ],

            "status": [
                "status",
                "policy_status",
            ],

            "section_title": [
                "section_title",
                "section",
                "section_name",
            ],
        }

        normalized = {}

        for target_key, possible_keys in (
            aliases.items()
        ):

            value = None

            for key in possible_keys:

                if metadata.get(key) is not None:

                    value = metadata.get(key)

                    break

                if result.get(key) is not None:

                    value = result.get(key)

                    break

            normalized[target_key] = value

        normalized["chunk_id"] = (
            metadata.get("chunk_id")
            or result.get("chunk_id")
            or result.get("id")
        )

        return normalized

    # ============================================================
    # POLICY ID RECOVERY
    # ============================================================

    @staticmethod
    def _derive_policy_id(
        policy_id: Any,
        policy_version_id: Any,
    ) -> Optional[str]:

        if policy_id:
            return str(
                policy_id
            )

        if not policy_version_id:
            return None

        version_id = str(
            policy_version_id
        ).strip()

        match = re.match(
            r"^(.*)-V(\d+)$",
            version_id,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        return None

    # ============================================================
    # DATABASE METADATA FALLBACK
    # ============================================================

    def _resolve_policy_metadata(
        self,
        db: Optional[Session],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:

        policy_id = self._derive_policy_id(
            metadata.get("policy_id"),
            metadata.get(
                "policy_version_id"
            ),
        )

        if policy_id:
            metadata["policy_id"] = (
                policy_id
            )

        if db is None or not policy_id:
            return metadata

        policy = (
            db.query(Policy)
            .filter(
                Policy.policy_id
                == policy_id
            )
            .first()
        )

        if policy is not None:

            if not metadata.get(
                "policy_name"
            ):
                metadata["policy_name"] = (
                    policy.policy_name
                )

            if not metadata.get(
                "category"
            ):
                metadata["category"] = (
                    policy.category
                )

            if not metadata.get(
                "department"
            ):
                metadata["department"] = (
                    policy.department
                )

        version_query = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_id
                == policy_id
            )
        )

        policy_version_id = (
            metadata.get(
                "policy_version_id"
            )
        )

        if policy_version_id:

            version_query = (
                version_query.filter(
                    PolicyVersion.policy_version_id
                    == policy_version_id
                )
            )

        else:

            version_number = (
                self._safe_int(
                    metadata.get(
                        "version_number"
                    )
                )
            )

            if version_number is not None:

                version_query = (
                    version_query.filter(
                        PolicyVersion.version_number
                        == version_number
                    )
                )

        policy_version = (
            version_query
            .order_by(
                PolicyVersion.version_number.desc()
            )
            .first()
        )

        if policy_version is not None:

            if not metadata.get(
                "policy_version_id"
            ):
                metadata[
                    "policy_version_id"
                ] = (
                    policy_version.policy_version_id
                )

            if metadata.get(
                "version_number"
            ) is None:
                metadata[
                    "version_number"
                ] = (
                    policy_version.version_number
                )

            if not metadata.get(
                "effective_date"
            ):
                metadata[
                    "effective_date"
                ] = (
                    policy_version.effective_date
                )

            if not metadata.get(
                "status"
            ):
                metadata[
                    "status"
                ] = (
                    policy_version.status
                )

        return metadata

    # ============================================================
    # EVIDENCE EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_evidence(
        result: Dict[str, Any],
    ) -> str:

        evidence = (
            result.get("document")
            or result.get("evidence")
            or result.get("text")
            or ""
        )

        return str(
            evidence
        ).strip()

    # ============================================================
    # TOPIC MATCHING
    # ============================================================

    def _phrase_match(
        self,
        text: str,
        phrase: str,
    ) -> bool:

        normalized_text = (
            self._normalize_text(text)
        )

        normalized_phrase = (
            self._normalize_text(phrase)
        )

        if (
            not normalized_text
            or not normalized_phrase
        ):
            return False

        return (
            normalized_phrase
            in normalized_text
        )

    def _topic_match_score(
        self,
        candidate: Dict[str, Any],
        topic_terms: List[str],
    ) -> float:

        if not topic_terms:
            return 0.0

        policy_name = (
            self._normalize_text(
                candidate.get(
                    "policy_name"
                )
            )
        )

        category = (
            self._normalize_text(
                candidate.get(
                    "category"
                )
            )
        )

        department = (
            self._normalize_text(
                candidate.get(
                    "department"
                )
            )
        )

        evidence = (
            self._normalize_text(
                candidate.get(
                    "evidence"
                )
            )
        )

        name_hits = 0
        evidence_hits = 0
        metadata_hits = 0

        for term in topic_terms:

            if self._phrase_match(
                policy_name,
                term,
            ):
                name_hits += 1

            if self._phrase_match(
                evidence,
                term,
            ):
                evidence_hits += 1

            if (
                self._phrase_match(
                    category,
                    term,
                )
                or self._phrase_match(
                    department,
                    term,
                )
            ):
                metadata_hits += 1

        candidate_tokens = self._tokenize(
            " ".join(
                [
                    policy_name,
                    category,
                    department,
                    evidence,
                ]
            )
        )

        topic_tokens = self._tokenize(
            " ".join(topic_terms)
        )

        token_overlap = 0.0

        if topic_tokens:

            token_overlap = (
                len(
                    candidate_tokens
                    & topic_tokens
                )
                / len(topic_tokens)
            )

        name_score = (
            name_hits
            / max(
                len(topic_terms),
                1,
            )
        )

        evidence_score = (
            evidence_hits
            / max(
                len(topic_terms),
                1,
            )
        )

        metadata_score = (
            metadata_hits
            / max(
                len(topic_terms),
                1,
            )
        )

        score = (
            0.35 * name_score
            + 0.40 * evidence_score
            + 0.15 * metadata_score
            + 0.10 * token_overlap
        )

        return round(
            min(
                max(score, 0.0),
                1.0,
            ),
            6,
        )

    # ============================================================
    # TOPIC-SPECIFIC EVIDENCE SCORE
    # ============================================================

    def _topic_evidence_score(
        self,
        evidence: str,
        topic_terms: List[str],
    ) -> float:

        if (
            not evidence
            or not topic_terms
        ):
            return 0.0

        normalized_evidence = (
            self._normalize_text(
                evidence
            )
        )

        weighted_matches = 0.0

        for term in topic_terms:

            normalized_term = (
                self._normalize_text(
                    term
                )
            )

            if not normalized_term:
                continue

            if (
                normalized_term
                in normalized_evidence
            ):

                if " " in normalized_term:
                    weighted_matches += 1.5
                else:
                    weighted_matches += 1.0

        score = (
            weighted_matches
            / max(
                len(topic_terms),
                1,
            )
        )

        return round(
            min(
                score,
                1.0,
            ),
            6,
        )

    # ============================================================
    # GENERIC EVIDENCE SCORE
    # ============================================================

    def _generic_evidence_score(
        self,
        evidence: str,
    ) -> float:

        if not evidence:
            return 1.0

        normalized = (
            self._normalize_text(
                evidence
            )
        )

        generic_hits = 0

        for term in self.GENERIC_TERMS:

            if self._phrase_match(
                normalized,
                term,
            ):
                generic_hits += 1

        score = (
            generic_hits
            / max(
                len(self.GENERIC_TERMS),
                1,
            )
        )

        return round(
            min(
                score * 3.0,
                1.0,
            ),
            6,
        )

    # ============================================================
    # SECTION SPECIFICITY
    # ============================================================

    def _section_specificity_score(
        self,
        matched_section: Optional[str],
        topic_evidence_score: float,
    ) -> float:

        if not matched_section:
            return 0.0

        section = (
            self._normalize_text(
                matched_section
            )
        )

        if section in self.GENERIC_SECTIONS:

            if topic_evidence_score >= 0.25:
                return 0.35

            return 0.0

        return 1.0

    # ============================================================
    # NORMALIZE CANDIDATE
    # ============================================================

    def normalize_candidate(
        self,
        result: Dict[str, Any],
        topic_terms: Optional[List[str]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:

        metadata = (
            self._extract_metadata(
                result
            )
        )

        metadata = (
            self._resolve_policy_metadata(
                db=db,
                metadata=metadata,
            )
        )

        evidence = (
            self._extract_evidence(
                result
            )
        )

        matched_section = (
            metadata.get(
                "section_title"
            )
            or metadata.get(
                "section"
            )
        )

        retrieval_score = (
            self._safe_float(
                result.get(
                    "rerank_score"
                )
            )
        )

        if retrieval_score == 0.0:
            retrieval_score = (
                self._safe_float(
                    result.get(
                        "relevance_score"
                    )
                )
            )

        if retrieval_score == 0.0:
            retrieval_score = (
                self._safe_float(
                    result.get(
                        "score"
                    )
                )
            )

        semantic_score = (
            self._safe_float(
                result.get(
                    "semantic_score"
                )
            )
        )

        lexical_score = (
            self._safe_float(
                result.get(
                    "lexical_score"
                )
            )
        )

        term_overlap_score = (
            self._safe_float(
                result.get(
                    "term_overlap_score"
                )
            )
        )

        section_score = (
            self._safe_float(
                result.get(
                    "section_score"
                )
            )
        )

        subject_score = (
            self._safe_float(
                result.get(
                    "subject_score"
                )
            )
        )

        if topic_terms is None:
            topic_terms = []

        preliminary = {
            "policy_name": metadata.get(
                "policy_name"
            ),
            "category": metadata.get(
                "category"
            ),
            "department": metadata.get(
                "department"
            ),
            "evidence": evidence,
        }

        topic_score = (
            self._topic_match_score(
                preliminary,
                topic_terms,
            )
        )

        topic_evidence_score = (
            self._topic_evidence_score(
                evidence,
                topic_terms,
            )
        )

        generic_evidence_score = (
            self._generic_evidence_score(
                evidence
            )
        )

        section_specificity_score = (
            self._section_specificity_score(
                matched_section,
                topic_evidence_score,
            )
        )

        retrieval_source = result.get(
            "_retrieval_source"
        )

        focused_bonus = (
            0.03
            if retrieval_source == "focused"
            else 0.0
        )

        generic_penalty = 0.0

        if (
            generic_evidence_score >= 0.20
            and topic_evidence_score < 0.12
        ):
            generic_penalty = 0.12

        final_score = (
            0.35 * retrieval_score
            + 0.25 * topic_score
            + 0.30 * topic_evidence_score
            + 0.10 * section_specificity_score
            + focused_bonus
            - generic_penalty
        )

        final_score = min(
            max(
                final_score,
                0.0,
            ),
            1.0,
        )

        return {
            "policy_id": self._derive_policy_id(
                metadata.get(
                    "policy_id"
                ),
                metadata.get(
                    "policy_version_id"
                ),
            ),

            "policy_name": metadata.get(
                "policy_name"
            ),

            "category": metadata.get(
                "category"
            ),

            "department": metadata.get(
                "department"
            ),

            "version_number": self._safe_int(
                metadata.get(
                    "version_number"
                )
            ),

            "policy_version_id": (
                self._safe_string(
                    metadata.get(
                        "policy_version_id"
                    )
                )
            ),

            "effective_date": (
                self._safe_string(
                    metadata.get(
                        "effective_date"
                    )
                )
            ),

            "status": self._safe_string(
                metadata.get(
                    "status"
                )
            ),

            "retrieval_score": round(
                retrieval_score,
                6,
            ),

            "semantic_score": round(
                semantic_score,
                6,
            ),

            "lexical_score": round(
                lexical_score,
                6,
            ),

            "term_overlap_score": round(
                term_overlap_score,
                6,
            ),

            "section_score": round(
                section_score,
                6,
            ),

            "subject_score": round(
                subject_score,
                6,
            ),

            "topic_score": round(
                topic_score,
                6,
            ),

            "topic_evidence_score": round(
                topic_evidence_score,
                6,
            ),

            "generic_evidence_score": round(
                generic_evidence_score,
                6,
            ),

            "section_specificity_score": round(
                section_specificity_score,
                6,
            ),

            "relevance_score": round(
                final_score,
                6,
            ),

            "matched_section": (
                self._safe_string(
                    matched_section
                )
            ),

            "evidence": evidence,

            "_chunk_id": metadata.get(
                "chunk_id"
            ),

            "_retrieval_source": (
                retrieval_source
            ),

            "_generic_penalty": (
                generic_penalty
            ),
        }

    # ============================================================
    # CANDIDATE FILTERING
    # ============================================================

    def _is_meaningfully_relevant(
        self,
        candidate: Dict[str, Any],
        best_topic_score: float,
        best_topic_evidence: float,
    ) -> bool:

        topic_score = self._safe_float(
            candidate.get(
                "topic_score"
            )
        )

        topic_evidence = self._safe_float(
            candidate.get(
                "topic_evidence_score"
            )
        )

        retrieval_score = self._safe_float(
            candidate.get(
                "retrieval_score"
            )
        )

        final_score = self._safe_float(
            candidate.get(
                "relevance_score"
            )
        )

        generic_score = self._safe_float(
            candidate.get(
                "generic_evidence_score"
            )
        )

        if topic_score >= 0.20:
            return True

        if topic_evidence >= 0.18:
            return True

        relative_topic = (
            topic_score
            >= max(
                0.05,
                best_topic_score * 0.35,
            )
        )

        relative_evidence = (
            topic_evidence
            >= max(
                0.04,
                best_topic_evidence * 0.30,
            )
        )

        if (
            relative_topic
            and relative_evidence
        ):
            return True

        if (
            retrieval_score >= 0.35
            and topic_score >= 0.08
            and topic_evidence >= 0.05
        ):
            return True

        if (
            generic_score >= 0.20
            and topic_evidence < 0.12
        ):
            return False

        return (
            final_score >= 0.25
            and topic_score >= 0.08
        )

    # ============================================================
    # POLICY DEDUPLICATION
    # ============================================================

    def _deduplicate_candidates(
        self,
        candidates: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:

        grouped = {}

        for candidate in candidates:

            policy_id = candidate.get(
                "policy_id"
            )

            if not policy_id:

                chunk_id = candidate.get(
                    "_chunk_id"
                )

                if chunk_id:
                    policy_id = (
                        "_chunk_"
                        + str(chunk_id)
                    )

                else:
                    policy_id = (
                        "_unknown_"
                        + str(
                            len(grouped)
                        )
                    )

            existing = grouped.get(
                policy_id
            )

            if existing is None:

                grouped[
                    policy_id
                ] = candidate

                continue

            candidate_score = (
                self._safe_float(
                    candidate.get(
                        "relevance_score"
                    )
                )
            )

            existing_score = (
                self._safe_float(
                    existing.get(
                        "relevance_score"
                    )
                )
            )

            candidate_topic = (
                self._safe_float(
                    candidate.get(
                        "topic_evidence_score"
                    )
                )
            )

            existing_topic = (
                self._safe_float(
                    existing.get(
                        "topic_evidence_score"
                    )
                )
            )

            if (
                candidate_score > existing_score
                or (
                    candidate_score
                    == existing_score
                    and candidate_topic
                    > existing_topic
                )
            ):

                grouped[
                    policy_id
                ] = candidate

        unique_candidates = list(
            grouped.values()
        )

        unique_candidates.sort(
            key=lambda item: (
                self._safe_float(
                    item.get(
                        "relevance_score"
                    )
                ),
                self._safe_float(
                    item.get(
                        "topic_evidence_score"
                    )
                ),
                self._safe_float(
                    item.get(
                        "topic_score"
                    )
                ),
            ),
            reverse=True,
        )

        final_candidates = []

        for candidate in unique_candidates[:top_k]:

            clean_candidate = {
                key: value
                for key, value
                in candidate.items()
                if not key.startswith("_")
            }

            final_candidates.append(
                clean_candidate
            )

        return final_candidates

    # ============================================================
    # PHASE 2F.1 MAIN OPERATION
    # ============================================================

    def analyze_regulatory_change(
        self,
        db: Session,
        regulatory_change_id: str,
        top_k: int = 10,
    ) -> Dict[str, Any]:

        if top_k < 1:
            raise ValueError(
                "top_k must be greater than or equal to 1."
            )

        regulatory_change = (
            self.get_regulatory_change(
                db=db,
                regulatory_change_id=(
                    regulatory_change_id
                ),
            )
        )

        if regulatory_change is None:

            raise ValueError(
                f"Regulatory change "
                f"'{regulatory_change_id}' "
                f"was not found."
            )

        topic_terms = (
            self._expand_topic(
                regulatory_change
            )
        )

        raw_results = (
            self.retrieve_candidate_policies(
                regulatory_change=(
                    regulatory_change
                ),
                top_k=top_k,
            )
        )

        normalized_candidates = []

        for result in raw_results:

            candidate = (
                self.normalize_candidate(
                    result=result,
                    topic_terms=topic_terms,
                    db=db,
                )
            )

            normalized_candidates.append(
                candidate
            )

        best_topic_score = max(
            (
                self._safe_float(
                    item.get(
                        "topic_score"
                    )
                )
                for item
                in normalized_candidates
            ),
            default=0.0,
        )

        best_topic_evidence = max(
            (
                self._safe_float(
                    item.get(
                        "topic_evidence_score"
                    )
                )
                for item
                in normalized_candidates
            ),
            default=0.0,
        )

        filtered_candidates = []

        for candidate in normalized_candidates:

            if self._is_meaningfully_relevant(
                candidate=candidate,
                best_topic_score=(
                    best_topic_score
                ),
                best_topic_evidence=(
                    best_topic_evidence
                ),
            ):

                filtered_candidates.append(
                    candidate
                )

        if not filtered_candidates:

            normalized_candidates.sort(
                key=lambda item: (
                    self._safe_float(
                        item.get(
                            "relevance_score"
                        )
                    ),
                    self._safe_float(
                        item.get(
                            "topic_score"
                        )
                    ),
                    self._safe_float(
                        item.get(
                            "topic_evidence_score"
                        )
                    ),
                ),
                reverse=True,
            )

            filtered_candidates = (
                normalized_candidates[
                    :max(
                        1,
                        min(
                            top_k,
                            len(
                                normalized_candidates
                            ),
                        ),
                    )
                ]
            )

        candidates = (
            self._deduplicate_candidates(
                candidates=(
                    filtered_candidates
                ),
                top_k=top_k,
            )
        )

        return {
            "regulatory_change_id": (
                regulatory_change
                .regulatory_change_id
            ),

            "regulatory_act": (
                regulatory_change
                .regulatory_act
            ),

            "change_topic": (
                regulatory_change
                .change_topic
            ),

            "change_description": (
                regulatory_change
                .change_description
            ),

            "topic_terms": topic_terms,

            "candidate_count": len(
                candidates
            ),

            "candidates": candidates,
        }

    # ============================================================
    # PHASE 2F.2
    # LEGAL EVIDENCE
    # ============================================================

    def retrieve_legal_evidence(
        self,
        regulatory_change: RegulatoryChange,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:

        try:

            from app.services.legal_retrieval_service import (
                get_legal_retrieval_service,
            )

            service = (
                get_legal_retrieval_service()
            )

            query = (
                self.build_policy_query(
                    regulatory_change
                )
            )

            kwargs = {
                "query": query,
                "top_k": top_k,
            }

            act_title = getattr(
                regulatory_change,
                "regulatory_act",
                None,
            )

            if act_title:
                kwargs["act_title"] = (
                    act_title
                )

            try:

                results = service.retrieve(
                    **kwargs
                )

            except TypeError:

                kwargs.pop(
                    "act_title",
                    None,
                )

                results = service.retrieve(
                    **kwargs
                )

            return results or []

        except Exception as exc:

            print(
                "WARNING: Legal retrieval failed:",
                exc,
            )

            return []

    def _legal_evidence_for_change(
        self,
        regulatory_change: RegulatoryChange,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:

        results = (
            self.retrieve_legal_evidence(
                regulatory_change,
                top_k,
            )
        )

        evidence = []

        for result in results:

            if not isinstance(
                result,
                dict,
            ):
                continue

            metadata = result.get(
                "metadata"
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            text = (
                result.get(
                    "document"
                )
                or result.get(
                    "evidence"
                )
                or result.get(
                    "text"
                )
                or ""
            )

            evidence.append(
                {
                    "chunk_id": (
                        metadata.get(
                            "chunk_id"
                        )
                        or result.get(
                            "chunk_id"
                        )
                        or result.get(
                            "id"
                        )
                    ),

                    "act_title": (
                        metadata.get(
                            "act_title"
                        )
                        or result.get(
                            "act_title"
                        )
                        or getattr(
                            regulatory_change,
                            "regulatory_act",
                            None,
                        )
                    ),

                    "document": (
                        metadata.get(
                            "document"
                        )
                        or result.get(
                            "document_name"
                        )
                    ),

                    "version": (
                        metadata.get(
                            "version"
                        )
                        or result.get(
                            "version"
                        )
                    ),

                    "effective_date": (
                        metadata.get(
                            "effective_date"
                        )
                        or result.get(
                            "effective_date"
                        )
                    ),

                    "similarity": self._safe_float(
                        result.get(
                            "similarity"
                        )
                        if result.get(
                            "similarity"
                        ) is not None
                        else result.get(
                            "score"
                        )
                    ),

                    "evidence": (
                        self._clean_evidence_text(
                            text
                        )
                    ),
                }
            )

        return evidence

    # ============================================================
    # PHASE 2F.2
    # POLICY RELATIONSHIPS
    # ============================================================

    def _relationship_rows(
        self,
        db: Session,
    ) -> List[Dict[str, Any]]:

        rows = []

        try:

            relationships = (
                db.query(
                    PolicyRelationship
                ).all()
            )

        except Exception as exc:

            print(
                "WARNING: Could not load "
                "policy relationships:",
                exc,
            )

            return rows

        for relationship in relationships:

            source = getattr(
                relationship,
                "source_policy_id",
                None,
            )

            target = getattr(
                relationship,
                "target_policy_id",
                None,
            )

            relationship_type = getattr(
                relationship,
                "relationship_type",
                None,
            )

            if source and target:

                rows.append(
                    {
                        "relationship_id": (
                            getattr(
                                relationship,
                                "relationship_id",
                                None,
                            )
                        ),

                        "source_policy_id": str(
                            source
                        ),

                        "target_policy_id": str(
                            target
                        ),

                        "relationship_type": (
                            str(
                                relationship_type
                            )
                            if relationship_type
                            is not None
                            else "related"
                        ),
                    }
                )

        return rows

    def _find_related_policies(
        self,
        db: Session,
        direct_policy_ids: Set[str],
    ) -> Dict[
        str,
        List[Dict[str, Any]]
    ]:

        related = {}

        if not direct_policy_ids:
            return related

        for row in (
            self._relationship_rows(db)
        ):

            source = (
                row["source_policy_id"]
            )

            target = (
                row["target_policy_id"]
            )

            if (
                source
                in direct_policy_ids
                and target
                not in direct_policy_ids
            ):

                related.setdefault(
                    target,
                    [],
                ).append(
                    {
                        "via_policy_id": source,
                        "relationship_type": (
                            row[
                                "relationship_type"
                            ]
                        ),
                        "relationship_id": (
                            row[
                                "relationship_id"
                            ]
                        ),
                    }
                )

            if (
                target
                in direct_policy_ids
                and source
                not in direct_policy_ids
            ):

                related.setdefault(
                    source,
                    [],
                ).append(
                    {
                        "via_policy_id": target,
                        "relationship_type": (
                            row[
                                "relationship_type"
                            ]
                        ),
                        "relationship_id": (
                            row[
                                "relationship_id"
                            ]
                        ),
                    }
                )

        return related

    # ============================================================
    # PHASE 2F.2
    # DIRECT IMPACT CLASSIFICATION
    # ============================================================

    def _classify_direct_candidates(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        direct = []

        for candidate in candidates:

            relevance = (
                self._safe_float(
                    candidate.get(
                        "relevance_score"
                    )
                )
            )

            topic_score = (
                self._safe_float(
                    candidate.get(
                        "topic_score"
                    )
                )
            )

            topic_evidence = (
                self._safe_float(
                    candidate.get(
                        "topic_evidence_score"
                    )
                )
            )

            # Direct impact requires strong evidence.
            is_direct = (
                topic_evidence >= 0.28
                or topic_score >= 0.30
                or (
                    relevance >= 0.42
                    and topic_evidence >= 0.15
                )
            )

            if is_direct:

                item = dict(
                    candidate
                )

                item[
                    "impact_status"
                ] = "direct"

                confidence = (
                    0.45 * relevance
                    + 0.30 * topic_score
                    + 0.25 * topic_evidence
                )

                item[
                    "impact_confidence"
                ] = round(
                    min(
                        1.0,
                        confidence,
                    ),
                    6,
                )

                direct.append(
                    item
                )

        return direct

    # ============================================================
    # IMPACT TYPE
    # ============================================================

    @staticmethod
    def _contains_any(
        text: str,
        terms: List[str],
    ) -> bool:

        normalized = text.lower()

        return any(
            term.lower()
            in normalized
            for term in terms
        )

    def _infer_impact_type(
        self,
        regulatory_change: RegulatoryChange,
        candidate: Dict[str, Any],
        impact_status: str,
    ) -> str:

        if impact_status == "no_impact":
            return "none"

        text = " ".join(
            [
                str(
                    getattr(
                        regulatory_change,
                        "change_topic",
                        "",
                    )
                    or ""
                ),

                str(
                    getattr(
                        regulatory_change,
                        "change_description",
                        "",
                    )
                    or ""
                ),

                str(
                    candidate.get(
                        "policy_name"
                    )
                    or ""
                ),

                str(
                    candidate.get(
                        "category"
                    )
                    or ""
                ),

                str(
                    candidate.get(
                        "evidence"
                    )
                    or ""
                ),
            ]
        ).lower()

        if self._contains_any(
            text,
            [
                "record",
                "records",
                "recordkeeping",
                "retention",
                "retained",
                "archive",
                "archival",
                "disposal",
                "deletion",
                "delete",
                "destroy",
            ],
        ):
            return "recordkeeping"

        if self._contains_any(
            text,
            [
                "document",
                "documentation",
                "evidence",
                "audit trail",
                "report",
                "reporting",
                "disclosure",
            ],
        ):
            return "documentation"

        if self._contains_any(
            text,
            [
                "process",
                "procedure",
                "workflow",
                "handling",
                "response",
                "recruitment",
                "selection",
                "payroll",
                "procurement",
                "planning",
            ],
        ):
            return "process"

        return "compliance"

    # ============================================================
    # EXPECTED ACTION
    # ============================================================

    @staticmethod
    def _infer_expected_action(
        impact_status: str,
        impact_type: str,
    ) -> str:

        if impact_status == "direct":
            return "review_required"

        if impact_status == "indirect":
            return "monitor"

        return "no_change_expected"

    # ============================================================
    # COMPANY POLICY EVIDENCE
    # ============================================================

    def _retrieve_policy_evidence(
        self,
        candidate: Dict[str, Any],
        regulatory_change: RegulatoryChange,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:

        policy_id = candidate.get(
            "policy_id"
        )

        if not policy_id:
            return []

        query = (
            f"{regulatory_change.change_topic or ''} "
            f"{regulatory_change.change_description or ''} "
            f"{candidate.get('policy_name') or ''} "
            f"{candidate.get('evidence') or ''}"
        )

        try:

            results = (
                self.policy_retrieval.retrieve(
                    query=query,
                    top_k=max(
                        3,
                        top_k,
                    ),
                    policy_id=policy_id,
                    status="active",
                )
            )

        except TypeError:

            try:

                results = (
                    self.policy_retrieval.retrieve(
                        query=query,
                        top_k=max(
                            3,
                            top_k,
                        ),
                        policy_id=policy_id,
                    )
                )

            except Exception:
                return []

        except Exception:
            return []

        evidence = []

        for result in (
            results or []
        ):

            if not isinstance(
                result,
                dict,
            ):
                continue

            metadata = result.get(
                "metadata"
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            text = (
                result.get(
                    "document"
                )
                or result.get(
                    "evidence"
                )
                or result.get(
                    "text"
                )
                or ""
            )

            evidence.append(
                {
                    "section": (
                        metadata.get(
                            "section_title"
                        )
                        or metadata.get(
                            "section"
                        )
                        or result.get(
                            "section_title"
                        )
                    ),

                    "version_number": (
                        metadata.get(
                            "version_number"
                        )
                        or result.get(
                            "version_number"
                        )
                    ),

                    "policy_version_id": (
                        metadata.get(
                            "policy_version_id"
                        )
                        or result.get(
                            "policy_version_id"
                        )
                    ),

                    "similarity": (
                        self._safe_float(
                            result.get(
                                "rerank_score"
                            )
                            if result.get(
                                "rerank_score"
                            ) is not None
                            else result.get(
                                "score"
                            )
                        )
                    ),

                    "evidence": (
                        self._clean_evidence_text(
                            text
                        )
                    ),
                }
            )

        return evidence[:top_k]

    # ============================================================
    # EXPLANATION
    # ============================================================

    def _build_impact_reason(
        self,
        regulatory_change: RegulatoryChange,
        candidate: Dict[str, Any],
        impact_status: str,
        impact_type: str,
        relationship_context: Optional[
            List[Dict[str, Any]]
        ] = None,
    ) -> str:

        topic = (
            getattr(
                regulatory_change,
                "change_topic",
                None,
            )
            or "the regulatory change"
        )

        policy_name = (
            candidate.get(
                "policy_name"
            )
            or candidate.get(
                "policy_id"
            )
            or "the company policy"
        )

        evidence = (
            self._clean_evidence_text(
                candidate.get(
                    "evidence"
                )
                or "",
                limit=500,
            )
        )

        if impact_status == "direct":

            return (
                f"The regulatory change concerns "
                f"{topic}. "
                f"{policy_name} contains "
                f"topic-specific policy evidence "
                f"that overlaps with the changed "
                f"requirement, so the policy should "
                f"be reviewed for "
                f"{impact_type} impact. "
                f"Retrieved policy evidence: "
                f"{evidence}"
            )

        if impact_status == "indirect":

            relation_text = ""

            if relationship_context:

                first = (
                    relationship_context[0]
                )

                relation_text = (
                    f" It is related to "
                    f"{first.get('via_policy_id')} "
                    f"through the "
                    f"{first.get('relationship_type')} "
                    f"relationship."
                )

            return (
                f"The policy does not appear to "
                f"be the primary policy affected "
                f"by {topic}, but it is connected "
                f"to a directly affected policy."
                f"{relation_text} "
                f"The recommended action is to "
                f"monitor the dependency and "
                f"review it if the primary policy "
                f"changes."
            )

        return (
            f"No sufficiently strong evidence "
            f"was found linking "
            f"{policy_name} to {topic}. "
            f"No policy change is currently "
            f"expected."
        )

    # ============================================================
    # PHASE 2F.2 MAIN OPERATION
    # ============================================================

    def analyze_impact(
        self,
        db: Session,
        regulatory_change_id: str,
        top_k: int = 10,
        legal_top_k: int = 5,
    ) -> Dict[str, Any]:

        if top_k < 1:
            raise ValueError(
                "top_k must be >= 1."
            )

        regulatory_change = (
            self.get_regulatory_change(
                db=db,
                regulatory_change_id=(
                    regulatory_change_id
                ),
            )
        )

        if regulatory_change is None:

            raise ValueError(
                f"Regulatory change "
                f"'{regulatory_change_id}' "
                f"was not found."
            )

        # --------------------------------------------------------
        # Phase 2F.1
        # --------------------------------------------------------

        phase_2f1 = (
            self.analyze_regulatory_change(
                db=db,
                regulatory_change_id=(
                    regulatory_change_id
                ),
                top_k=top_k,
            )
        )

        candidates = (
            phase_2f1.get(
                "candidates",
                [],
            )
        )

        # --------------------------------------------------------
        # Direct impact
        # --------------------------------------------------------

        direct_candidates = (
            self._classify_direct_candidates(
                candidates
            )
        )

        direct_policy_ids = {
            str(
                candidate.get(
                    "policy_id"
                )
            )
            for candidate
            in direct_candidates
            if candidate.get(
                "policy_id"
            )
        }

        # --------------------------------------------------------
        # Relationship graph
        # --------------------------------------------------------

        related = (
            self._find_related_policies(
                db=db,
                direct_policy_ids=(
                    direct_policy_ids
                ),
            )
        )

        candidate_by_policy = {
            str(
                candidate.get(
                    "policy_id"
                )
            ): candidate
            for candidate
            in candidates
            if candidate.get(
                "policy_id"
            )
        }

        impacts = []

        # ========================================================
        # DIRECT IMPACTS
        # ========================================================

        for candidate in direct_candidates:

            policy_id = str(
                candidate[
                    "policy_id"
                ]
            )

            impact_type = (
                self._infer_impact_type(
                    regulatory_change=(
                        regulatory_change
                    ),
                    candidate=candidate,
                    impact_status="direct",
                )
            )

            policy_evidence = (
                self._retrieve_policy_evidence(
                    candidate=candidate,
                    regulatory_change=(
                        regulatory_change
                    ),
                    top_k=3,
                )
            )

            impacts.append(
                {
                    "policy_id": policy_id,

                    "policy_name": candidate.get(
                        "policy_name"
                    ),

                    "category": candidate.get(
                        "category"
                    ),

                    "department": candidate.get(
                        "department"
                    ),

                    "version_number": candidate.get(
                        "version_number"
                    ),

                    "policy_version_id": (
                        candidate.get(
                            "policy_version_id"
                        )
                    ),

                    "effective_date": candidate.get(
                        "effective_date"
                    ),

                    "status": candidate.get(
                        "status"
                    ),

                    "impact_status": "direct",

                    "impact_confidence": (
                        candidate.get(
                            "impact_confidence",
                            0.0,
                        )
                    ),

                    "impact_type": impact_type,

                    "expected_action": (
                        self._infer_expected_action(
                            "direct",
                            impact_type,
                        )
                    ),

                    "relevance_score": (
                        candidate.get(
                            "relevance_score",
                            0.0,
                        )
                    ),

                    "topic_score": (
                        candidate.get(
                            "topic_score",
                            0.0,
                        )
                    ),

                    "topic_evidence_score": (
                        candidate.get(
                            "topic_evidence_score",
                            0.0,
                        )
                    ),

                    "matched_section": (
                        candidate.get(
                            "matched_section"
                        )
                    ),

                    "policy_evidence": (
                        policy_evidence
                    ),

                    "retrieved_policy_evidence": (
                        self._clean_evidence_text(
                            candidate.get(
                                "evidence"
                            )
                            or "",
                            limit=1200,
                        )
                    ),

                    "relationship_context": [],

                    "reason": (
                        self._build_impact_reason(
                            regulatory_change=(
                                regulatory_change
                            ),
                            candidate=candidate,
                            impact_status="direct",
                            impact_type=impact_type,
                        )
                    ),
                }
            )

        # ========================================================
        # INDIRECT IMPACTS
        # ========================================================

        direct_ids = {
            str(
                item["policy_id"]
            )
            for item in impacts
            if item.get(
                "impact_status"
            ) == "direct"
        }

        for (
            policy_id,
            relationship_context,
        ) in related.items():

            if policy_id in direct_ids:
                continue

            candidate = (
                candidate_by_policy.get(
                    policy_id
                )
            )

            # ----------------------------------------------------
            # Policy not already in retrieval candidates
            # ----------------------------------------------------

            if candidate is None:

                base_policy = (
                    db.query(
                        Policy
                    )
                    .filter(
                        Policy.policy_id
                        == policy_id
                    )
                    .first()
                )

                if base_policy is None:
                    continue

                candidate = {
                    "policy_id": (
                        base_policy.policy_id
                    ),

                    "policy_name": (
                        base_policy.policy_name
                    ),

                    "category": (
                        base_policy.category
                    ),

                    "department": (
                        base_policy.department
                    ),

                    "version_number": None,

                    "policy_version_id": None,

                    "effective_date": None,

                    "status": None,

                    "relevance_score": 0.0,

                    "topic_score": 0.0,

                    "topic_evidence_score": 0.0,

                    "matched_section": None,

                    "evidence": "",
                }

                # Get latest version
                try:

                    version = (
                        db.query(
                            PolicyVersion
                        )
                        .filter(
                            PolicyVersion.policy_id
                            == policy_id
                        )
                        .order_by(
                            PolicyVersion
                            .version_number
                            .desc()
                        )
                        .first()
                    )

                    if version is not None:

                        candidate[
                            "version_number"
                        ] = (
                            version
                            .version_number
                        )

                        candidate[
                            "policy_version_id"
                        ] = (
                            version
                            .policy_version_id
                        )

                        candidate[
                            "effective_date"
                        ] = (
                            self._safe_string(
                                version
                                .effective_date
                            )
                        )

                        candidate[
                            "status"
                        ] = (
                            version.status
                        )

                except Exception:
                    pass

            impact_type = (
                self._infer_impact_type(
                    regulatory_change=(
                        regulatory_change
                    ),
                    candidate=candidate,
                    impact_status="indirect",
                )
            )

            policy_evidence = (
                self._retrieve_policy_evidence(
                    candidate=candidate,
                    regulatory_change=(
                        regulatory_change
                    ),
                    top_k=2,
                )
            )

            impacts.append(
                {
                    "policy_id": policy_id,

                    "policy_name": candidate.get(
                        "policy_name"
                    ),

                    "category": candidate.get(
                        "category"
                    ),

                    "department": candidate.get(
                        "department"
                    ),

                    "version_number": candidate.get(
                        "version_number"
                    ),

                    "policy_version_id": (
                        candidate.get(
                            "policy_version_id"
                        )
                    ),

                    "effective_date": candidate.get(
                        "effective_date"
                    ),

                    "status": candidate.get(
                        "status"
                    ),

                    "impact_status": "indirect",

                    "impact_confidence": 0.5,

                    "impact_type": impact_type,

                    "expected_action": (
                        self._infer_expected_action(
                            "indirect",
                            impact_type,
                        )
                    ),

                    "relevance_score": (
                        candidate.get(
                            "relevance_score",
                            0.0,
                        )
                    ),

                    "topic_score": (
                        candidate.get(
                            "topic_score",
                            0.0,
                        )
                    ),

                    "topic_evidence_score": (
                        candidate.get(
                            "topic_evidence_score",
                            0.0,
                        )
                    ),

                    "matched_section": (
                        candidate.get(
                            "matched_section"
                        )
                    ),

                    "policy_evidence": (
                        policy_evidence
                    ),

                    "retrieved_policy_evidence": (
                        self._clean_evidence_text(
                            candidate.get(
                                "evidence"
                            )
                            or "",
                            limit=1000,
                        )
                    ),

                    "relationship_context": (
                        relationship_context
                    ),

                    "reason": (
                        self._build_impact_reason(
                            regulatory_change=(
                                regulatory_change
                            ),
                            candidate=candidate,
                            impact_status="indirect",
                            impact_type=impact_type,
                            relationship_context=(
                                relationship_context
                            ),
                        )
                    ),
                }
            )

        # ========================================================
        # LEGAL EVIDENCE
        # ========================================================

        legal_evidence = (
            self._legal_evidence_for_change(
                regulatory_change=(
                    regulatory_change
                ),
                top_k=legal_top_k,
            )
        )

        # ========================================================
        # SORT RESULTS
        # ========================================================

        status_order = {
            "direct": 0,
            "indirect": 1,
            "no_impact": 2,
        }

        impacts.sort(
            key=lambda item: (
                status_order.get(
                    item.get(
                        "impact_status"
                    ),
                    99,
                ),

                -self._safe_float(
                    item.get(
                        "impact_confidence"
                    )
                ),

                -self._safe_float(
                    item.get(
                        "relevance_score"
                    )
                ),
            )
        )

        direct_count = sum(
            1
            for item
            in impacts
            if item.get(
                "impact_status"
            ) == "direct"
        )

        indirect_count = sum(
            1
            for item
            in impacts
            if item.get(
                "impact_status"
            ) == "indirect"
        )

        return {
            "regulatory_change_id": (
                regulatory_change
                .regulatory_change_id
            ),

            "regulatory_act": (
                regulatory_change
                .regulatory_act
            ),

            "change_topic": (
                regulatory_change
                .change_topic
            ),

            "change_description": (
                regulatory_change
                .change_description
            ),

            "legal_evidence": (
                legal_evidence
            ),

            "candidate_count": len(
                candidates
            ),

            "direct_impact_count": (
                direct_count
            ),

            "indirect_impact_count": (
                indirect_count
            ),

            "impact_count": len(
                impacts
            ),

            "impacts": impacts,
        }

    # ============================================================
    # CLEAN EVIDENCE
    # ============================================================

    @staticmethod
    def _clean_evidence_text(
        value: Any,
        limit: int = 1800,
    ) -> str:

        if value is None:
            return ""

        text = re.sub(
            r"\s+",
            " ",
            str(value).strip(),
        )

        if len(text) > limit:

            return (
                text[:limit].rstrip()
                + "..."
            )

        return text

    # ============================================================
    # SAFE CONVERSION HELPERS
    # ============================================================

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float:

        if value is None:
            return 0.0

        try:
            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> Optional[int]:

        if value is None:
            return None

        if isinstance(
            value,
            int,
        ):
            return value

        text = str(
            value
        ).strip()

        if text.lower().startswith(
            "v"
        ):
            text = text[1:]

        try:

            return int(
                text
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _safe_string(
        value: Any,
    ) -> Optional[str]:

        if value is None:
            return None

        return str(
            value
        )


# ================================================================
# SINGLETON
# ================================================================

_service_instance: Optional[
    ImpactAnalysisService
] = None


def get_impact_analysis_service() -> ImpactAnalysisService:

    global _service_instance

    if _service_instance is None:

        _service_instance = (
            ImpactAnalysisService()
        )

    return _service_instance