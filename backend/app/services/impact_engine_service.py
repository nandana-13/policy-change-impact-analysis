from __future__ import annotations


from collections import defaultdict

from typing import Any, Dict, List, Optional, Tuple


from sqlalchemy.orm import Session


from app.database import SessionLocal


from app.models.policy import Policy

from app.models.policy_relationship import PolicyRelationship

from app.models.policy_version import PolicyVersion

from app.models.regulatory_change import RegulatoryChange


from app.services.impact_analysis_service import (
    get_impact_analysis_service,
)


from app.services.legal_retrieval_service import (
    LegalRetrievalService,
)


class ImpactEngineService:
    """
    PolicyLens Phase 2F.2

    Direct & Indirect Regulatory Impact Analysis

    Pipeline:

        Regulatory Change
                |
                v
        Phase 2F.1 Candidate Policies
                |
                v
        Legal Evidence Retrieval
                |
                v
        Company Policy Evidence
                |
                v
        Direct Impact Classification
                |
                v
        Policy Relationship Graph
                |
                v
        Indirect Impact Classification
                |
                v
        Impact Type
                |
                v
        Expected Action
                |
                v
        Evidence-backed Result

    LLM-generated explanation is intentionally NOT implemented here.

    That belongs to the later Explainable RAG generation phase.
    """

    # ================================================================
    # TOPIC SYNONYMS
    # ================================================================

    TOPIC_SYNONYMS = {

        "data_retention": [

            "data retention",

            "retention",

            "retain",

            "retained",

            "record retention",

            "records retention",

            "record keeping",

            "recordkeeping",

            "storage period",

            "retention period",

            "data storage",

            "archive",

            "archiving",

            "disposal",

            "dispose",

            "delete",

            "deletion",

            "destroy",

            "destruction",

        ],


        "data_protection": [

            "data protection",

            "personal data",

            "personal information",

            "privacy",

            "data processing",

            "processing personal data",

            "data subject",

            "data security",

            "privacy protection",

        ],


        "equality": [

            "equality",

            "equal opportunity",

            "equal opportunities",

            "non discrimination",

            "nondiscrimination",

            "discrimination",

            "fair treatment",

            "equal treatment",

            "workplace equality",

        ],


        "financial_reporting": [

            "financial reporting",

            "financial report",

            "financial statements",

            "accounting",

            "reporting requirements",

            "disclosure",

            "disclosures",

            "annual report",

            "financial records",

        ],


        "tax_compliance": [

            "tax",

            "tax compliance",

            "tax reporting",

            "tax return",

            "tax returns",

            "tax records",

            "tax obligation",

            "tax obligations",

        ],


        "employment": [

            "employment",

            "employee",

            "employees",

            "workplace",

            "employment practices",

            "human resources",

            "hr",

            "staff",

            "personnel",

        ],


        "health_and_safety": [

            "health and safety",

            "workplace safety",

            "occupational safety",

            "safety",

            "hazard",

            "hazards",

            "risk assessment",

        ],


        "incident_response": [

            "incident response",

            "security incident",

            "incident management",

            "breach",

            "data breach",

            "incident reporting",

            "incident investigation",

        ],

    }


    # ================================================================
    # INITIALIZATION
    # ================================================================

    def __init__(self):

        print("Initializing Impact Engine...")


        self.candidate_service = get_impact_analysis_service()


        self.legal_retrieval = LegalRetrievalService()


        print("Impact Engine initialized.")


    # ================================================================
    # BASIC HELPERS
    # ================================================================

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        if value is None:

            return default


        try:

            return float(value)

        except (TypeError, ValueError):

            return default


    @staticmethod
    def _clean_text(value: Any) -> str:

        if value is None:

            return ""


        return " ".join(
            str(value).split()
        ).strip()


    @staticmethod
    def _normalize(value: Any) -> str:

        return (
            ImpactEngineService
            ._clean_text(value)
            .lower()
        )


    @staticmethod
    def _get_text(
        item: Dict[str, Any],
        *keys: str,
    ) -> str:
        """
        Extract text from retrieval results.

        IMPORTANT:

        PolicyRetrievalService returns the actual policy chunk
        under `evidence`.

        LegalRetrievalService returns the actual legal chunk
        under `evidence_text`.

        We therefore support:

            content
            evidence
            evidence_text
            text
            document_text
            document

        """

        for key in keys:

            value = item.get(key)


            if value is not None:

                cleaned = ImpactEngineService._clean_text(value)


                if cleaned:

                    return cleaned


        return ""


    # ================================================================
    # TOPIC HELPERS
    # ================================================================

    @classmethod
    def _topic_terms(
        cls,
        topic: Any,
    ) -> List[str]:


        normalized_topic = cls._normalize(topic)


        if not normalized_topic:

            return []


        terms = [
            normalized_topic
        ]


        readable_topic = (
            normalized_topic
            .replace("_", " ")
            .replace("-", " ")
        )


        if readable_topic not in terms:

            terms.append(readable_topic)


        configured = cls.TOPIC_SYNONYMS.get(
            normalized_topic,
            [],
        )


        for term in configured:

            normalized_term = cls._normalize(term)


            if (
                normalized_term
                and normalized_term not in terms
            ):

                terms.append(normalized_term)


        return terms


    @classmethod
    def calculate_topic_match(
        cls,
        topic: Any,
        policy_evidence: List[Dict[str, Any]],
        policy_name: str = "",
    ) -> float:


        terms = cls._topic_terms(topic)


        if not terms:

            return 0.0


        evidence_text = " ".join(

            cls._get_text(
                item,

                "content",

                "evidence",

                "evidence_text",

                "text",

                "document_text",

                "document",

            )

            for item in policy_evidence

        )


        combined_text = " ".join(
            [
                cls._normalize(policy_name),

                cls._normalize(evidence_text),
            ]
        ).strip()


        if not combined_text:

            return 0.0


        matched_terms = 0


        for term in terms:

            if not term:

                continue


            if term in combined_text:

                matched_terms += 1


        if matched_terms == 0:

            return 0.0


        denominator = max(
            3.0,
            min(
                float(len(terms)),
                6.0,
            ),
        )


        return min(
            1.0,
            matched_terms / denominator,
        )


    # ================================================================
    # DATABASE
    # ================================================================

    def _get_db(self) -> Session:

        return SessionLocal()


    # ================================================================
    # REGULATORY CHANGE
    # ================================================================

    def get_regulatory_change(
        self,
        db: Session,
        regulatory_change_id: str,
    ) -> Optional[RegulatoryChange]:


        return (
            db.query(
                RegulatoryChange
            )
            .filter(
                RegulatoryChange.regulatory_change_id
                == regulatory_change_id
            )
            .first()
        )


    # ================================================================
    # LEGAL ACT MAPPING
    # ================================================================

    @staticmethod
    def _map_act_title(
        regulatory_act: Optional[str],
    ) -> Optional[str]:


        if not regulatory_act:

            return None


        act = (
            str(regulatory_act)
            .strip()
            .lower()
        )


        mapping = {

            "data_protection_act_2018":
                "Data Protection Act 2018",


            "equality_act_2010":
                "Equality Act 2010",


            "finance_act_2003":
                "Finance Act 2003",


            "income_tax_earnings_and_pensions_act_2003":
                "Income Tax (Earnings and Pensions) Act 2003",


            "localism_act_2011":
                "Localism Act 2011",

        }


        return mapping.get(
            act,
            regulatory_act,
        )


    # ================================================================
    # LEGAL EVIDENCE
    # ================================================================

    def retrieve_legal_evidence(
        self,
        regulatory_change: RegulatoryChange,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:


        query_parts = []


        regulatory_act = self._clean_text(
            getattr(
                regulatory_change,
                "regulatory_act",
                "",
            )
        )


        change_topic = self._clean_text(
            getattr(
                regulatory_change,
                "change_topic",
                "",
            )
        )


        change_description = self._clean_text(
            getattr(
                regulatory_change,
                "change_description",
                "",
            )
        )


        if regulatory_act:

            query_parts.append(
                regulatory_act
            )


        if change_topic:

            query_parts.append(
                change_topic
            )


        if change_description:

            query_parts.append(
                change_description
            )


        query = " ".join(
            query_parts
        ).strip()


        act_title = self._map_act_title(
            regulatory_act
        )


        try:

            result = self.legal_retrieval.retrieve(
                query=query,
                top_k=top_k,
                act_title=act_title,
            )


        except Exception:

            try:

                result = self.legal_retrieval.retrieve(
                    query=query,
                    top_k=top_k,
                )

            except Exception:

                result = []


        raw_results = result


        if isinstance(result, dict):

            for key in (
                "results",
                "evidence",
                "items",
                "documents",
            ):

                value = result.get(key)


                if isinstance(value, list):

                    raw_results = value

                    break


        if not isinstance(
            raw_results,
            list,
        ):

            return []


        evidence = []


        for item in raw_results:


            if not isinstance(
                item,
                dict,
            ):

                continue


            # Some retrieval services may nest metadata
            # inside "source".

            source = item.get("source")


            if not isinstance(
                source,
                dict,
            ):

                source = {}


            # --------------------------------------------------------
            # IMPORTANT LEGAL RAG FIX
            # --------------------------------------------------------
            #
            # LegalRetrievalService returns the actual legal text
            # under:
            #
            #     "evidence_text"
            #
            # It returns the Chroma document identifier under:
            #
            #     "document"
            #
            # Therefore "document" must NOT be preferred as evidence
            # text when evidence_text is available.
            #
            # --------------------------------------------------------

            content = self._get_text(
                item,

                "evidence_text",

                "content",

                "evidence",

                "text",

                "document_text",

            )


            if not content:

                content = self._get_text(
                    source,

                    "evidence_text",

                    "content",

                    "evidence",

                    "text",

                    "document_text",

                )


            similarity = item.get(
                "similarity"
            )


            if similarity is None:

                similarity = item.get(
                    "similarity_score"
                )


            if similarity is None:

                similarity = item.get(
                    "relevance_score"
                )


            if similarity is None:

                similarity = source.get(
                    "similarity"
                )


            if similarity is None:

                similarity = source.get(
                    "similarity_score"
                )


            evidence.append(
                {

                    "chunk_id":
                        item.get(
                            "chunk_id"
                        )
                        or source.get(
                            "chunk_id"
                        ),


                    "act_title":
                        item.get(
                            "act_title"
                        )
                        or source.get(
                            "act_title"
                        ),


                    "document":
                        item.get(
                            "document"
                        )
                        or source.get(
                            "document"
                        ),


                    "version":
                        item.get(
                            "version"
                        )
                        or source.get(
                            "version"
                        ),


                    "effective_date":
                        item.get(
                            "effective_date"
                        )
                        or source.get(
                            "effective_date"
                        ),


                    "category":
                        item.get(
                            "category"
                        )
                        or source.get(
                            "category"
                        ),


                    "content_type":
                        item.get(
                            "content_type"
                        )
                        or source.get(
                            "content_type"
                        ),


                    "source":
                        source
                        if source
                        else item.get(
                            "source"
                        ),


                    "jurisdiction":
                        item.get(
                            "jurisdiction"
                        )
                        or source.get(
                            "jurisdiction"
                        ),


                    "file_path":
                        item.get(
                            "file_path"
                        )
                        or source.get(
                            "file_path"
                        ),


                    "act_uri":
                        item.get(
                            "act_uri"
                        )
                        or source.get(
                            "act_uri"
                        ),


                    "chunk_index":
                        item.get(
                            "chunk_index"
                        )
                        or source.get(
                            "chunk_index"
                        ),


                    "similarity":
                        self._safe_float(
                            similarity
                        ),


                    "content":
                        content,

                    "evidence_text":
                        content,

                }
            )


        print(
            "[Impact Engine] "
            f"Legal evidence normalized: {len(evidence)}"
        )

        print(
            "[Impact Engine] "
            "Legal evidence text lengths="
            f"{[len(item.get('content', '')) for item in evidence]}"
        )

        return evidence


    # ================================================================
    # PHASE 2F.1 CANDIDATE POLICIES
    # ================================================================

    def get_candidate_policies(
        self,
        db: Session,
        regulatory_change: RegulatoryChange,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:


        result = (
            self.candidate_service
            .analyze_regulatory_change(
                db=db,
                regulatory_change_id=(
                    regulatory_change
                    .regulatory_change_id
                ),
                top_k=top_k,
            )
        )


        if isinstance(
            result,
            dict,
        ):

            candidates = result.get(
                "candidates",
                [],
            )

        else:

            candidates = getattr(
                result,
                "candidates",
                [],
            )


        normalized = []


        for candidate in candidates:


            if hasattr(
                candidate,
                "model_dump",
            ):

                candidate = (
                    candidate.model_dump()
                )


            elif hasattr(
                candidate,
                "dict",
            ):

                candidate = (
                    candidate.dict()
                )


            if isinstance(
                candidate,
                dict,
            ):

                normalized.append(
                    candidate
                )


        return normalized


    # ================================================================
    # POLICY QUERY
    # ================================================================

    def build_policy_query(
        self,
        regulatory_change: RegulatoryChange,
    ) -> str:


        parts = []


        regulatory_act = self._clean_text(
            getattr(
                regulatory_change,
                "regulatory_act",
                "",
            )
        )


        change_topic = self._clean_text(
            getattr(
                regulatory_change,
                "change_topic",
                "",
            )
        )


        change_description = self._clean_text(
            getattr(
                regulatory_change,
                "change_description",
                "",
            )
        )


        if regulatory_act:

            parts.append(
                regulatory_act
            )


        if change_topic:

            parts.append(
                change_topic
            )


        if change_description:

            parts.append(
                change_description
            )


        # Add topic synonyms to improve lexical
        # and semantic retrieval.

        topic_terms = self._topic_terms(
            change_topic
        )


        for term in topic_terms[:8]:

            if term not in parts:

                parts.append(term)


        return " ".join(
            parts
        ).strip()


    # ================================================================
    # POLICY EVIDENCE
    # ================================================================

    def retrieve_policy_evidence(
        self,
        policy_id: str,
        regulatory_change: RegulatoryChange,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:


        query = self.build_policy_query(
            regulatory_change
        )


        try:

            result = (
                self.candidate_service
                .policy_retrieval
                .retrieve(
                    query=query,
                    top_k=max(
                        top_k,
                        10,
                    ),
                    policy_id=policy_id,
                )
            )


        except Exception as exc:

            print(
                f"Policy evidence retrieval failed "
                f"for {policy_id}: {exc}"
            )


            return []


        raw_results = result


        if isinstance(
            result,
            dict,
        ):

            for key in (
                "results",
                "evidence",
                "items",
                "documents",
            ):

                value = result.get(key)


                if isinstance(
                    value,
                    list,
                ):

                    raw_results = value

                    break


        if not isinstance(
            raw_results,
            list,
        ):

            return []


        evidence = []


        for item in raw_results:


            if not isinstance(
                item,
                dict,
            ):

                continue


            item_policy_id = item.get(
                "policy_id"
            )


            if (
                item_policy_id
                and item_policy_id != policy_id
            ):

                continue


            # ========================================================
            # POLICY EVIDENCE
            # ========================================================
            #
            # PolicyRetrievalService returns:
            #
            #     "evidence": document
            #
            # Therefore evidence must be accepted here.
            #
            # ========================================================

            content = self._get_text(
                item,

                "content",

                "evidence",

                "evidence_text",

                "text",

                "document_text",

                "document",

            )


            similarity = item.get(
                "similarity"
            )


            if similarity is None:

                similarity = item.get(
                    "rerank_score"
                )


            if similarity is None:

                similarity = item.get(
                    "relevance_score"
                )


            evidence.append(
                {

                    "chunk_id":
                        item.get(
                            "chunk_id"
                        ),


                    "policy_id":
                        item.get(
                            "policy_id"
                        )
                        or policy_id,


                    "policy_name":
                        item.get(
                            "policy_name"
                        ),


                    "policy_version_id":
                        item.get(
                            "policy_version_id"
                        ),


                    "version_number":
                        item.get(
                            "version_number"
                        ),


                    "effective_date":
                        item.get(
                            "effective_date"
                        ),


                    "status":
                        item.get(
                            "status"
                        ),


                    "section_index":
                        item.get(
                            "section_index"
                        ),


                    "section_title":
                        item.get(
                            "section_title"
                        ),


                    "similarity":
                        self._safe_float(
                            similarity
                        ),


                    "content":
                        content,


                    "evidence":
                        content,


                    "file_path":
                        item.get(
                            "file_path"
                        ),

                }
            )


            if len(evidence) >= top_k:

                break


        return evidence


    # ================================================================
    # EVIDENCE ALIGNMENT
    # ================================================================

    def calculate_evidence_alignment(
        self,
        legal_evidence: List[Dict[str, Any]],
        policy_evidence: List[Dict[str, Any]],
    ) -> float:


        if not legal_evidence:

            return 0.0


        if not policy_evidence:

            return 0.0


        legal_text = " ".join(

            self._get_text(
                item,

                "content",

                "evidence",

                "evidence_text",

                "text",

                "document_text",

                "document",

            )

            for item in legal_evidence

        )


        policy_text = " ".join(

            self._get_text(
                item,

                "content",

                "evidence",

                "evidence_text",

                "text",

                "document_text",

                "document",

            )

            for item in policy_evidence

        )


        legal_words = {

            word

            for word in self._normalize(
                legal_text
            ).split()

            if len(word) >= 4

        }


        policy_words = {

            word

            for word in self._normalize(
                policy_text
            ).split()

            if len(word) >= 4

        }


        if not legal_words:

            return 0.0


        if not policy_words:

            return 0.0


        intersection = (
            legal_words
            .intersection(
                policy_words
            )
        )


        union = (
            legal_words
            .union(
                policy_words
            )
        )


        if not union:

            return 0.0


        jaccard = (
            len(intersection)
            / len(union)
        )


        return min(
            1.0,
            jaccard * 4.0,
        )


    # ================================================================
    # DIRECT SCORE
    # ================================================================

    def calculate_direct_score(
        self,
        candidate: Dict[str, Any],
        policy_evidence: List[Dict[str, Any]],
        legal_evidence: List[Dict[str, Any]],
        regulatory_change: Optional[
            RegulatoryChange
        ] = None,
    ) -> float:


        relevance = self._safe_float(
            candidate.get(
                "relevance_score"
            )
        )


        semantic = self._safe_float(
            candidate.get(
                "semantic_score"
            )
        )


        lexical = self._safe_float(
            candidate.get(
                "lexical_score"
            )
        )


        term_overlap = self._safe_float(
            candidate.get(
                "term_overlap_score"
            )
        )


        topic_evidence = self._safe_float(
            candidate.get(
                "topic_evidence_score"
            )
        )


        policy_name = self._clean_text(
            candidate.get(
                "policy_name",
                ""
            )
        )


        topic = ""


        if regulatory_change is not None:

            topic = getattr(
                regulatory_change,
                "change_topic",
                "",
            )


        topic_match = self.calculate_topic_match(
            topic=topic,
            policy_evidence=policy_evidence,
            policy_name=policy_name,
        )


        alignment = (
            self.calculate_evidence_alignment(
                legal_evidence,
                policy_evidence,
            )
        )


        # ============================================================
        # DIRECT IMPACT SCORE
        # ============================================================
        #
        # Relevance       25%
        # Semantic        10%
        # Lexical         10%
        # Term overlap     5%
        # Topic evidence  10%
        # Topic match     15%
        # Evidence align  25%
        #
        # Explicit topic matching and actual evidence are now
        # stronger signals than generic similarity alone.
        # ============================================================

        score = (

            0.25 * relevance

            + 0.10 * semantic

            + 0.10 * lexical

            + 0.05 * term_overlap

            + 0.10 * topic_evidence

            + 0.15 * topic_match

            + 0.25 * alignment

        )


        return max(
            0.0,
            min(
                1.0,
                score,
            ),
        )


    # ================================================================
    # DIRECT CLASSIFICATION
    # ================================================================

    def classify_direct_impact(
        self,
        score: float,
    ) -> str:


        if score >= 0.40:

            return "direct"


        if score >= 0.20:

            return "review"


        return "no_direct_impact"
    
    # ================================================================
# POLICY RELATIONSHIP GRAPH
# ================================================================

    def build_relationship_graph(
        self,
        db: Session,
    ) -> Dict[
        str,
        List[Dict[str, Any]],
    ]:


        relationships = (
            db.query(
                PolicyRelationship
            )
            .all()
        )


        graph = defaultdict(list)


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


            relationship_id = getattr(
                relationship,
                "relationship_id",
                None,
            )


            if not source or not target:

                continue


            graph[source].append(
                {
                    "policy_id": target,

                    "relationship_type":
                        relationship_type,

                    "relationship_id":
                        relationship_id,

                    "source_policy_id":
                        source,

                    "target_policy_id":
                        target,
                }
            )


        return graph


# ================================================================
# INDIRECT IMPACT
# ================================================================

    def find_indirect_impacts(
        self,
        direct_policy_ids: List[str],
        relationship_graph: Dict[
            str,
            List[Dict[str, Any]],
        ],
    ) -> List[Dict[str, Any]]:


        direct_set = set(
            direct_policy_ids
        )


        visited = set(
            direct_policy_ids
        )


        queue: List[
            Tuple[str, int, Optional[str]]
        ] = [

            (
                policy_id,
                0,
                None,
            )

            for policy_id
            in direct_policy_ids

        ]


        indirect = []


        while queue:


            current_policy, depth, parent = (
                queue.pop(0)
            )


            if depth >= 2:

                continue


            relationships = (
                relationship_graph.get(
                    current_policy,
                    [],
                )
            )


            for relationship in relationships:


                target = relationship.get(
                    "target_policy_id"
                )


                if not target:

                    target = relationship.get(
                        "policy_id"
                    )


                if not target:

                    continue


                if target in visited:

                    continue


                visited.add(target)


                next_depth = depth + 1


                indirect.append(
                    {
                        "policy_id":
                            target,


                        "relationship_id":
                            relationship.get(
                                "relationship_id"
                            ),


                        "relationship_type":
                            relationship.get(
                                "relationship_type"
                            ),


                        "source_policy_id":
                            relationship.get(
                                "source_policy_id"
                            )
                            or current_policy,


                        "target_policy_id":
                            relationship.get(
                                "target_policy_id"
                            )
                            or target,


                        "relationship_depth":
                            next_depth,
                    }
                )


                queue.append(
                    (
                        target,
                        next_depth,
                        current_policy,
                    )
                )


        # Never classify a direct policy as indirect.
        return [

            item

            for item in indirect

            if item.get(
                "policy_id"
            ) not in direct_set

        ]


# ================================================================
# IMPACT TYPE
# ================================================================

    def determine_impact_type(
        self,
        regulatory_change: RegulatoryChange,
        policy_evidence: List[Dict[str, Any]],
        classification: str,
    ) -> str:


        if classification == "no_impact":

            return "none"


        topic = self._normalize(
            getattr(
                regulatory_change,
                "change_topic",
                "",
            )
        )


        description = self._normalize(
            getattr(
                regulatory_change,
                "change_description",
                "",
            )
        )


        text = " ".join(
            [
                topic,

                description,

                " ".join(

                    self._get_text(
                        item,

                        "content",

                        "evidence",

                        "evidence_text",

                        "text",

                        "document_text",

                        "document",

                    )

                    for item in policy_evidence

                ),

            ]

        )


        if any(
            term in text

            for term in [

                "retention",

                "retain",

                "records",

                "record keeping",

                "recordkeeping",

                "storage period",

                "disposal",

                "archive",

                "archiving",

            ]

        ):

            return "recordkeeping"


        if any(
            term in text

            for term in [

                "documentation",

                "document",

                "policy wording",

                "procedure",

                "guidance",

            ]

        ):

            return "documentation"


        if any(
            term in text

            for term in [

                "process",

                "processing",

                "workflow",

                "operation",

                "operational",

            ]

        ):

            return "process"


        return "documentation"


# ================================================================
# EXPECTED ACTION
# ================================================================

    def determine_expected_action(
        self,
        classification: str,
        impact_type: str,
        score: float = 0.0,
    ) -> str:


        if classification == "direct":

            return "review_required"


        if classification == "indirect":

            return "review_required"


        if classification == "review":

            return "review_required"


        return "no_change_expected"


# ================================================================
# POLICY METADATA
# ================================================================

    def get_policy_metadata(
        self,
        db: Session,
        policy_id: str,
    ) -> Dict[str, Any]:


        policy = (
            db.query(
                Policy
            )
            .filter(
                Policy.policy_id
                == policy_id
            )
            .first()
        )


        if policy is None:

            return {

                "policy_id":
                    policy_id,

                "policy_name":
                    policy_id,

                "category":
                    None,

                "department":
                    None,

            }


        return {

            "policy_id":
                policy.policy_id,

            "policy_name":
                policy.policy_name,

            "category":
                policy.category,

            "department":
                policy.department,

        }


# ================================================================
# POLICY VERSION
# ================================================================

    def get_latest_policy_version(
        self,
        db: Session,
        policy_id: str,
    ) -> Optional[Dict[str, Any]]:


        version = (
            db.query(
                PolicyVersion
            )
            .filter(
                PolicyVersion.policy_id
                == policy_id
            )
            .order_by(
                PolicyVersion.version_number.desc()
            )
            .first()
        )


        if version is None:

            return None


        return {

            "policy_version_id":
                version.policy_version_id,

            "version_number":
                version.version_number,

            "effective_date":
                (
                    str(
                        version.effective_date
                    )
                    if version.effective_date
                    else None
                ),

            "status":
                version.status,

        }


# ================================================================
# REASON
# ================================================================

    def build_reason(
        self,
        regulatory_change: RegulatoryChange,
        policy_name: str,
        impact_classification: str,
        impact_type: str,
        relationship_type: Optional[str] = None,
    ) -> str:


        topic = self._clean_text(
            getattr(
                regulatory_change,
                "change_topic",
                "",
            )
        )


        description = self._clean_text(
            getattr(
                regulatory_change,
                "change_description",
                "",
            )
        )


        if impact_classification == "direct":


            return (

                f"{policy_name} has a direct potential impact "

                f"because the regulatory change concerns "

                f"{topic or 'the identified regulatory topic'}. "

                f"Retrieved policy evidence aligns with the "

                f"regulatory change and indicates that the "

                f"policy should be reviewed. "

                f"Impact type: {impact_type}. "

                f"Change description: {description}"

            )


        if impact_classification == "indirect":


            relationship_text = ""


            if relationship_type:

                relationship_text = (

                    f" The relationship type is "

                    f"'{relationship_type}'."

                )


            return (

                f"{policy_name} may be indirectly affected "

                f"through its dependency relationship with "

                f"another impacted policy.{relationship_text} "

                f"Impact type: {impact_type}."

            )


        return (

            f"Available retrieved evidence does not provide "

            f"sufficient support for a direct impact on "

            f"{policy_name} from the regulatory change "

            f"concerning {topic or 'the identified topic'}. "

            f"The policy is therefore currently classified "

            f"as no impact."

        )


# ================================================================
# CREATE IMPACT ITEM
# ================================================================

    def _build_impact_item(
        self,
        db: Session,
        regulatory_change: RegulatoryChange,
        policy_id: str,
        classification: str,
        impact_score: float,
        policy_evidence: List[
            Dict[str, Any]
        ],
        relationship: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:


        metadata = (
            self.get_policy_metadata(
                db=db,
                policy_id=policy_id,
            )
        )


        version = (
            self.get_latest_policy_version(
                db=db,
                policy_id=policy_id,
            )
        )


        relationship_type = None

        relationships = []


        if relationship:


            relationship_type = relationship.get(
                "relationship_type"
            )


            relationships.append(
                {
                    "relationship_id":
                        relationship.get(
                            "relationship_id"
                        ),

                    "relationship_type":
                        relationship.get(
                            "relationship_type"
                        ),

                    "source_policy_id":
                        relationship.get(
                            "source_policy_id"
                        ),

                    "target_policy_id":
                        relationship.get(
                            "target_policy_id"
                        )
                        or policy_id,

                    "relationship_depth":
                        relationship.get(
                            "relationship_depth"
                        ),
                }
            )


        impact_type = (
            self.determine_impact_type(
                regulatory_change=
                    regulatory_change,

                policy_evidence=
                    policy_evidence,

                classification=
                    classification,
            )
        )


        expected_action = (
            self.determine_expected_action(
                classification=
                    classification,

                impact_type=
                    impact_type,

                score=
                    impact_score,
            )
        )


        return {

            **metadata,

            **(
                version
                or {}
            ),


            "impact_classification":
                classification,


            "impact_score":
                round(
                    impact_score,
                    6,
                ),


            "impact_type":
                impact_type,


            "expected_action":
                expected_action,


            "reason":
                self.build_reason(
                    regulatory_change=
                        regulatory_change,

                    policy_name=
                        metadata[
                            "policy_name"
                        ],

                    impact_classification=
                        classification,

                    impact_type=
                        impact_type,

                    relationship_type=
                        relationship_type,
                ),


            "policy_evidence":
                policy_evidence,


            "relationships":
                relationships,

        }
    # ================================================================
# MAIN ANALYSIS
# ================================================================

    def analyze_regulatory_change(
        self,
        regulatory_change_id: Optional[str] = None,
        db: Optional[Session] = None,
        regulatory_change: Optional[
            RegulatoryChange
        ] = None,
        top_k: int = 10,
        legal_top_k: int = 5,
        policy_evidence_top_k: int = 3,
    ) -> Dict[str, Any]:


        owns_session = False


        if db is None:

            db = self._get_db()

            owns_session = True


        try:

            # ========================================================
            # 1. RESOLVE REGULATORY CHANGE
            # ========================================================

            if regulatory_change is None:

                if not regulatory_change_id:

                    raise ValueError(
                        "regulatory_change_id is required."
                    )


                regulatory_change = (
                    self.get_regulatory_change(
                        db=db,
                        regulatory_change_id=
                            regulatory_change_id,
                    )
                )


            if regulatory_change is None:

                raise ValueError(
                    f"Regulatory change "
                    f"'{regulatory_change_id}' "
                    f"was not found."
                )


            # ========================================================
            # 2. LEGAL EVIDENCE
            # ========================================================

            print(
                "Retrieving legal evidence..."
            )


            legal_evidence = (
                self.retrieve_legal_evidence(
                    regulatory_change=
                        regulatory_change,

                    top_k=
                        legal_top_k,
                )
            )


            print(
                f"Legal evidence retrieved: "
                f"{len(legal_evidence)}"
            )


            # Debug legal evidence text lengths
            if legal_evidence:

                legal_text_lengths = [

                    len(
                        self._get_text(
                            item,

                            "content",

                            "evidence",

                            "evidence_text",

                            "text",

                            "document_text",

                        )
                    )

                    for item
                    in legal_evidence

                ]

                print(
                    f"[Impact Engine] "
                    f"Legal evidence lengths="
                    f"{legal_text_lengths}"
                )

            else:

                print(
                    "[Impact Engine] "
                    "No legal evidence text retrieved."
                )


            # ========================================================
            # 3. CANDIDATE POLICIES
            # ========================================================

            print(
                "Retrieving candidate policies..."
            )


            candidates = (
                self.get_candidate_policies(
                    db=db,
                    regulatory_change=
                        regulatory_change,
                    top_k=top_k,
                )
            )


            print(
                f"Candidate policies: "
                f"{len(candidates)}"
            )


            # ========================================================
            # 4. RELATIONSHIP GRAPH
            # ========================================================

            print(
                "Building policy relationship graph..."
            )


            relationship_graph = (
                self.build_relationship_graph(
                    db=db
                )
            )


            # ========================================================
            # 5. DIRECT IMPACT
            # ========================================================

            direct_items = []

            direct_policy_ids = []


            # Keep review candidates separately so that
            # they are NOT accidentally converted into
            # no_impact with score 0.

            review_items = []


            analysed_policy_ids = set()


            for candidate in candidates:


                policy_id = candidate.get(
                    "policy_id"
                )


                if not policy_id:

                    continue


                analysed_policy_ids.add(
                    policy_id
                )


                policy_evidence = (
                    self.retrieve_policy_evidence(
                        policy_id=
                            policy_id,

                        regulatory_change=
                            regulatory_change,

                        top_k=
                            policy_evidence_top_k,
                    )
                )


                # Debug information.

                print(
                    f"[Impact Engine] "
                    f"{policy_id}: "
                    f"policy evidence="
                    f"{len(policy_evidence)}"
                )


                if policy_evidence:

                    text_lengths = [

                        len(
                            self._get_text(
                                item,

                                "content",

                                "evidence",

                                "evidence_text",

                                "text",

                                "document_text",

                                "document",

                            )
                        )

                        for item
                        in policy_evidence

                    ]


                    print(
                        f"[Impact Engine] "
                        f"{policy_id}: "
                        f"evidence lengths="
                        f"{text_lengths}"
                    )

                else:

                    print(
                        f"[Impact Engine] "
                        f"{policy_id}: "
                        f"No policy evidence."
                    )


                direct_score = (
                    self.calculate_direct_score(
                        candidate=
                            candidate,

                        policy_evidence=
                            policy_evidence,

                        legal_evidence=
                            legal_evidence,

                        regulatory_change=
                            regulatory_change,
                    )
                )


                classification = (
                    self.classify_direct_impact(
                        direct_score
                    )
                )


                print(
                    f"[Impact Engine] "
                    f"{policy_id}: "
                    f"score={direct_score:.4f}, "
                    f"classification="
                    f"{classification}"
                )


                if classification == "direct":

                    direct_policy_ids.append(
                        policy_id
                    )


                    direct_items.append(
                        self._build_impact_item(
                            db=db,

                            regulatory_change=
                                regulatory_change,

                            policy_id=
                                policy_id,

                            classification=
                                "direct",

                            impact_score=
                                direct_score,

                            policy_evidence=
                                policy_evidence,
                        )
                    )


                elif classification == "review":

                    review_items.append(
                        self._build_impact_item(
                            db=db,

                            regulatory_change=
                                regulatory_change,

                            policy_id=
                                policy_id,

                            # Review is exposed as a
                            # direct potential impact
                            # because it requires analyst
                            # review.

                            classification=
                                "direct",

                            impact_score=
                                direct_score,

                            policy_evidence=
                                policy_evidence,
                        )
                    )


            # ========================================================
            # 6. INDIRECT IMPACT
            # ========================================================

            indirect_candidates = (
                self.find_indirect_impacts(
                    direct_policy_ids=
                        direct_policy_ids,

                    relationship_graph=
                        relationship_graph,
                )
            )


            indirect_items = []


            direct_and_review_ids = set(
                direct_policy_ids
            )


            direct_and_review_ids.update(

                item.get(
                    "policy_id"
                )

                for item
                in review_items

            )


            for indirect in indirect_candidates:


                policy_id = indirect.get(
                    "policy_id"
                )


                if not policy_id:

                    continue


                if policy_id in direct_and_review_ids:

                    continue


                policy_evidence = (
                    self.retrieve_policy_evidence(
                        policy_id=
                            policy_id,

                        regulatory_change=
                            regulatory_change,

                        top_k=
                            policy_evidence_top_k,
                    )
                )


                indirect_items.append(
                    self._build_impact_item(
                        db=db,

                        regulatory_change=
                            regulatory_change,

                        policy_id=
                            policy_id,

                        classification=
                            "indirect",

                        impact_score=
                            0.25,

                        policy_evidence=
                            policy_evidence,

                        relationship=
                            indirect,
                    )
                )


            # ========================================================
            # 7. NO IMPACT
            # ========================================================

            impacted_ids = set(
                direct_policy_ids
            )


            impacted_ids.update(

                item.get(
                    "policy_id"
                )

                for item
                in review_items

            )


            impacted_ids.update(

                item.get(
                    "policy_id"
                )

                for item
                in indirect_items

            )


            no_impact_items = []


            for candidate in candidates:


                policy_id = candidate.get(
                    "policy_id"
                )


                if not policy_id:

                    continue


                if policy_id in impacted_ids:

                    continue


                policy_evidence = (
                    self.retrieve_policy_evidence(
                        policy_id=
                            policy_id,

                        regulatory_change=
                            regulatory_change,

                        top_k=
                            policy_evidence_top_k,
                    )
                )


                no_impact_items.append(
                    self._build_impact_item(
                        db=db,

                        regulatory_change=
                            regulatory_change,

                        policy_id=
                            policy_id,

                        classification=
                            "no_impact",

                        impact_score=
                            0.0,

                        policy_evidence=
                            policy_evidence,
                    )
                )


            # ========================================================
            # 8. COMBINE RESULTS
            # ========================================================

            impact_items = (

                direct_items

                + review_items

                + indirect_items

                + no_impact_items

            )


            priority = {

                "direct": 0,

                "indirect": 1,

                "no_impact": 2,

            }


            impact_items.sort(

                key=lambda item: (

                    priority.get(
                        item.get(
                            "impact_classification"
                        ),
                        99,
                    ),


                    -self._safe_float(
                        item.get(
                            "impact_score"
                        )
                    ),


                    item.get(
                        "policy_id",
                        "",
                    ),

                )

            )


            # ========================================================
            # 9. SUMMARY
            # ========================================================

            direct_count = sum(

                1

                for item
                in impact_items

                if item.get(
                    "impact_classification"
                ) == "direct"

            )


            indirect_count = sum(

                1

                for item
                in impact_items

                if item.get(
                    "impact_classification"
                ) == "indirect"

            )


            no_impact_count = sum(

                1

                for item
                in impact_items

                if item.get(
                    "impact_classification"
                ) == "no_impact"

            )


            return {

                "regulatory_change_id":
                    regulatory_change
                    .regulatory_change_id,


                "regulatory_act":
                    regulatory_change
                    .regulatory_act,


                "change_topic":
                    regulatory_change
                    .change_topic,


                "change_description":
                    regulatory_change
                    .change_description,


                "candidate_count":
                    len(candidates),


                "direct_impact_count":
                    direct_count,


                "indirect_impact_count":
                    indirect_count,


                "no_impact_count":
                    no_impact_count,


                "total_analysed":
                    len(impact_items),


                "legal_evidence":
                    legal_evidence,


                "impact_items":
                    impact_items,

            }


        finally:


            if owns_session:

                db.close()


# ====================================================================
# SINGLETON
# ====================================================================

_impact_engine_service: Optional[
    ImpactEngineService
] = None


def get_impact_engine_service(
) -> ImpactEngineService:


    global _impact_engine_service


    if _impact_engine_service is None:

        _impact_engine_service = (
            ImpactEngineService()
        )


    return _impact_engine_service