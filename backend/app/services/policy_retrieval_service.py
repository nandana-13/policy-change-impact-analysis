from pathlib import Path
from typing import Optional, List, Dict, Any
import pickle
import re

import chromadb
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class PolicyRetrievalService:
    """
    PolicyLens Phase 2E.3
    Intent-Aware + Hybrid Policy Retrieval

    Retrieval pipeline:

        Query
          ↓
        ChromaDB semantic candidates
          ↓
        Version/date filtering
          ↓
        TF-IDF lexical similarity
          ↓
        Query term overlap
          ↓
        Subject intent detection
          ↓
        Section intent detection
          ↓
        Metadata-aware reranking
          ↓
        Top evidence
    """

    def __init__(self):

        print("Loading company policy TF-IDF vectorizer...")

        # ---------------------------------------------------------
        # PROJECT PATHS
        # ---------------------------------------------------------

        self.project_root = Path(
            __file__
        ).resolve().parents[3]

        self.embedding_dir = (
            self.project_root
            / "data"
            / "processed"
            / "policy_rag"
            / "embeddings"
        )

        self.vectorizer_path = (
            self.embedding_dir
            / "tfidf_vectorizer.pkl"
        )

        self.svd_path = (
            self.embedding_dir
            / "svd_model.pkl"
        )

        self.chroma_path = (
            self.project_root
            / "data"
            / "vectorstore"
            / "policy_chroma"
        )

        # ---------------------------------------------------------
        # LOAD TF-IDF
        # ---------------------------------------------------------

        with open(
            self.vectorizer_path,
            "rb"
        ) as f:

            self.vectorizer = pickle.load(f)

        print(
            "Company policy TF-IDF vectorizer loaded."
        )

        # ---------------------------------------------------------
        # LOAD SVD
        # ---------------------------------------------------------

        print(
            "Loading company policy SVD model..."
        )

        with open(
            self.svd_path,
            "rb"
        ) as f:

            self.svd = pickle.load(f)

        print(
            "Company policy SVD model loaded."
        )

        # ---------------------------------------------------------
        # LOAD CHROMADB
        # ---------------------------------------------------------

        print(
            "Loading persistent company policy ChromaDB..."
        )

        self.chroma_client = (
            chromadb.PersistentClient(
                path=str(
                    self.chroma_path
                )
            )
        )

        self.collection = (
            self.chroma_client.get_collection(
                name="policylens_policies"
            )
        )

        print(
            "Company policy ChromaDB loaded."
        )

        print(
            f"Collection: {self.collection.name}"
        )

        print(
            f"Records: {self.collection.count()}"
        )

    # =============================================================
    # TEXT NORMALIZATION
    # =============================================================

    @staticmethod
    def _normalize_text(
        text: str
    ) -> str:

        """
        Normalize text for lexical comparison.
        """

        text = str(text).lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =============================================================
    # TOKENIZATION
    # =============================================================

    @staticmethod
    def _tokens(
        text: str
    ) -> set:

        """
        Return meaningful query/document tokens.
        """

        stopwords = {
            "what",
            "which",
            "how",
            "why",
            "when",
            "where",
            "does",
            "do",
            "are",
            "is",
            "the",
            "a",
            "an",
            "to",
            "of",
            "for",
            "and",
            "or",
            "in",
            "on",
            "with",
            "apply",
            "applies",
            "requirements",
            "requirement",
            "must",
            "should",
            "may",
            "be",
            "this",
            "that",
            "these",
            "those",
            "policy",
        }

        normalized = (
            PolicyRetrievalService
            ._normalize_text(text)
        )

        return {
            token
            for token in normalized.split()
            if (
                token not in stopwords
                and len(token) > 1
            )
        }

    # =============================================================
    # QUERY SUBJECT INTENT
    # =============================================================

    def _detect_subject_intent(
        self,
        query: str
    ) -> Dict[str, Any]:

        q = self._normalize_text(
            query
        )

        subjects = {

            "employee": [
                "employee",
                "employees",
                "staff",
                "worker",
                "workers",
                "personnel",
                "employee data",
            ],

            "customer": [
                "customer",
                "customers",
                "client",
                "clients",
                "customer data",
            ],

            "financial": [
                "financial",
                "finance",
                "financial reporting",
                "accounting",
                "accounts",
                "audit",
                "auditing",
                "tax",
                "taxation",
                "expense",
                "expenses",
                "payroll",
                "compensation",
                "earnings",
            ],

            "recruitment": [
                "recruitment",
                "recruiting",
                "hiring",
                "selection",
                "candidate",
                "candidates",
            ],

            "procurement": [
                "procurement",
                "supplier",
                "suppliers",
                "vendor",
                "vendors",
                "purchasing",
            ],

            "property": [
                "property",
                "planning",
                "development",
                "land",
            ],

            "community": [
                "community",
                "local community",
                "community engagement",
            ],
        }

        detected = []

        for subject, keywords in (
            subjects.items()
        ):

            for keyword in keywords:

                if keyword in q:

                    detected.append(
                        subject
                    )

                    break

        return {
            "subjects": detected
        }

    # =============================================================
    # SUBJECT RELEVANCE
    # =============================================================

    def _subject_relevance(
        self,
        query: str,
        metadata: Dict[str, Any],
        evidence: str
    ) -> float:

        intent = (
            self._detect_subject_intent(
                query
            )
        )

        subjects = intent[
            "subjects"
        ]

        if not subjects:
            return 0.0

        policy_name = (
            self._normalize_text(
                metadata.get(
                    "policy_name",
                    ""
                )
            )
        )

        category = (
            self._normalize_text(
                metadata.get(
                    "category",
                    ""
                )
            )
        )

        department = (
            self._normalize_text(
                metadata.get(
                    "department",
                    ""
                )
            )
        )

        evidence_text = (
            self._normalize_text(
                evidence
            )
        )

        combined = (
            policy_name
            + " "
            + category
            + " "
            + department
            + " "
            + evidence_text
        )

        score = 0.0

        # ---------------------------------------------------------
        # EMPLOYEE
        # ---------------------------------------------------------

        if "employee" in subjects:

            if "employee" in policy_name:

                score += 1.0

            elif "employee" in category:

                score += 0.8

            elif "employee" in combined:

                score += 0.5

            # Strongly penalize customer-specific policy.
            if (
                "customer" in policy_name
                and "employee" not in policy_name
            ):

                score -= 0.8

        # ---------------------------------------------------------
        # CUSTOMER
        # ---------------------------------------------------------

        if "customer" in subjects:

            if "customer" in policy_name:

                score += 1.0

            elif "customer" in category:

                score += 0.8

            elif "customer" in combined:

                score += 0.5

            if (
                "employee" in policy_name
                and "customer" not in policy_name
            ):

                score -= 0.8

        # ---------------------------------------------------------
        # FINANCIAL
        # ---------------------------------------------------------

        if "financial" in subjects:

            financial_terms = [
                "financial",
                "finance",
                "tax",
                "payroll",
                "expense",
                "audit",
                "reporting",
                "compensation",
                "earnings",
            ]

            matches = sum(
                1
                for term in financial_terms
                if term in combined
            )

            if matches >= 3:

                score += 1.0

            elif matches >= 2:

                score += 0.7

            elif matches >= 1:

                score += 0.4

        # ---------------------------------------------------------
        # RECRUITMENT
        # ---------------------------------------------------------

        if "recruitment" in subjects:

            recruitment_terms = [
                "recruitment",
                "recruiting",
                "hiring",
                "selection",
                "candidate",
            ]

            matches = sum(
                1
                for term in recruitment_terms
                if term in combined
            )

            if matches >= 2:

                score += 0.8

            elif matches == 1:

                score += 0.4

        # ---------------------------------------------------------
        # PROCUREMENT
        # ---------------------------------------------------------

        if "procurement" in subjects:

            procurement_terms = [
                "procurement",
                "supplier",
                "vendor",
                "purchasing",
            ]

            matches = sum(
                1
                for term in procurement_terms
                if term in combined
            )

            if matches >= 2:

                score += 0.8

            elif matches == 1:

                score += 0.4

        # ---------------------------------------------------------
        # PROPERTY
        # ---------------------------------------------------------

        if "property" in subjects:

            if (
                "property" in combined
                or "planning" in combined
            ):

                score += 0.8

        # ---------------------------------------------------------
        # COMMUNITY
        # ---------------------------------------------------------

        if "community" in subjects:

            if "community" in combined:

                score += 0.8

        return float(
            max(
                -1.0,
                min(
                    1.0,
                    score
                )
            )
        )

    # =============================================================
    # SECTION INTENT DETECTION
    # =============================================================

    def _detect_section_intent(
        self,
        query: str
    ) -> List[str]:

        q = self._normalize_text(
            query
        )

        intent_map = {

            # -----------------------------------------------------
            # RECORDS / RETENTION
            # -----------------------------------------------------

            "records_evidence": [
                "record",
                "records",
                "retention",
                "retain",
                "retaining",
                "disposal",
                "dispose",
                "archive",
                "archiving",
                "maintain records",
            ],

            # -----------------------------------------------------
            # MONITORING
            # -----------------------------------------------------

            "monitoring_review": [
                "monitor",
                "monitoring",
                "review",
                "reviews",
                "reviewing",
                "audit",
                "auditing",
                "assurance",
                "compliance check",
                "ongoing",
                "oversight",
            ],

            # -----------------------------------------------------
            # ROLES
            # -----------------------------------------------------

            "roles_responsibilities": [
                "responsibility",
                "responsibilities",
                "responsible",
                "owner",
                "owners",
                "role",
                "roles",
                "accountable",
                "accountability",
            ],

            # -----------------------------------------------------
            # EXCEPTIONS
            # -----------------------------------------------------

            "exceptions_escalation": [
                "exception",
                "exceptions",
                "escalation",
                "escalate",
                "waiver",
                "waivers",
                "non compliance",
                "noncompliance",
            ],

            # -----------------------------------------------------
            # RELATED POLICIES
            # -----------------------------------------------------

            "related_policies": [
                "related policy",
                "related policies",
                "dependency",
                "dependencies",
                "dependent",
                "related control",
                "related controls",
            ],

            # -----------------------------------------------------
            # VERSION CHANGES
            # -----------------------------------------------------

            "version_change": [
                "change",
                "changed",
                "changes",
                "changed from",
                "new requirement",
                "new requirements",
                "revised",
                "revision",
                "version",
                "updated",
                "update",
                "added",
                "removed",
            ],

            # -----------------------------------------------------
            # PURPOSE
            # -----------------------------------------------------

            "purpose": [
                "purpose",
                "objective",
                "objectives",
                "why does this policy exist",
            ],

            # -----------------------------------------------------
            # SCOPE
            # -----------------------------------------------------

            "scope": [
                "scope",
                "applies to",
                "who does this apply to",
                "coverage",
                "covered",
            ],

            # -----------------------------------------------------
            # REQUIREMENTS
            # -----------------------------------------------------

            "requirements": [
                "requirement",
                "requirements",
                "rules",
                "controls",
                "must",
                "required",
                "obligation",
                "obligations",
            ],
        }

        detected = []

        for intent, keywords in (
            intent_map.items()
        ):

            for keyword in keywords:

                if keyword in q:

                    detected.append(
                        intent
                    )

                    break

        return detected

    # =============================================================
    # SECTION RELEVANCE
    # =============================================================

    def _section_relevance(
        self,
        query: str,
        metadata: Dict[str, Any]
    ) -> float:

        intents = (
            self._detect_section_intent(
                query
            )
        )

        if not intents:
            return 0.0

        section_title = (
            self._normalize_text(
                metadata.get(
                    "section_title",
                    ""
                )
            )
        )

        if not section_title:
            return 0.0

        # ---------------------------------------------------------
        # IMPORTANT:
        #
        # We intentionally use precise section names here.
        #
        # "Control Evidence" should NOT automatically receive
        # the same score as "Records and Evidence".
        # ---------------------------------------------------------

        section_map = {

            "records_evidence": [
                "records and evidence",
            ],

            "monitoring_review": [
                "monitoring and review",
            ],

            "roles_responsibilities": [
                "roles and responsibilities",
            ],

            "exceptions_escalation": [
                "exceptions and escalation",
            ],

            "related_policies": [
                "related policies and controls",
            ],

            "version_change": [
                "version change summary",
            ],

            "purpose": [
                "purpose",
            ],

            "scope": [
                "scope",
            ],

            "requirements": [
                "policy requirements",
            ],
        }

        best_score = 0.0

        for intent in intents:

            matching_sections = (
                section_map.get(
                    intent,
                    []
                )
            )

            for section in matching_sections:

                if section_title == section:

                    best_score = max(
                        best_score,
                        1.0
                    )

                elif section in section_title:

                    best_score = max(
                        best_score,
                        0.8
                    )

        return float(
            min(
                1.0,
                best_score
            )
        )

    # =============================================================
    # LEXICAL SIMILARITY
    # =============================================================

    def _lexical_similarity(
        self,
        query: str,
        documents: List[str]
    ) -> np.ndarray:

        query_vector = (
            self.vectorizer.transform(
                [query]
            )
        )

        document_vectors = (
            self.vectorizer.transform(
                documents
            )
        )

        similarities = (
            cosine_similarity(
                query_vector,
                document_vectors
            )[0]
        )

        return similarities

    # =============================================================
    # TERM OVERLAP
    # =============================================================

    def _term_overlap(
        self,
        query: str,
        document: str
    ) -> float:

        query_terms = (
            self._tokens(query)
        )

        document_terms = (
            self._tokens(document)
        )

        if not query_terms:
            return 0.0

        overlap = (
            query_terms
            .intersection(
                document_terms
            )
        )

        return (
            len(overlap)
            / len(query_terms)
        )

    # =============================================================
    # BUILD CHROMA FILTER
    # =============================================================

    def _build_where_filter(
        self,
        policy_id: Optional[str] = None,
        version_number: Optional[int] = None,
        category: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """
        Build only ChromaDB-compatible filters.

        IMPORTANT:

        effective_date is stored as a string.

        ChromaDB does not support numeric comparison operators
        such as $lte on string metadata.

        Therefore as_of_date filtering is performed in Python
        after candidate retrieval.
        """

        conditions = []

        if policy_id:

            conditions.append({
                "policy_id": policy_id
            })

        if version_number is not None:

            conditions.append({
                "version_number": version_number
            })

        if category:

            conditions.append({
                "category": category
            })

        if department:

            conditions.append({
                "department": department
            })

        if status:

            conditions.append({
                "status": status
            })

        if not conditions:

            return None

        if len(conditions) == 1:

            return conditions[0]

        return {
            "$and": conditions
        }

    # =============================================================
    # AS-OF DATE FILTER
    # =============================================================

    def _filter_by_as_of_date(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        distances: List[float],
        as_of_date: Optional[str],
    ):

        """
        Apply version-aware effective-date filtering.

        Only records satisfying:

            effective_date <= as_of_date

        are retained.

        Dates are expected in ISO format:

            YYYY-MM-DD

        Therefore lexical comparison is safe.
        """

        if not as_of_date:

            return (
                documents,
                metadatas,
                distances
            )

        filtered_documents = []
        filtered_metadatas = []
        filtered_distances = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):

            effective_date = metadata.get(
                "effective_date"
            )

            if not effective_date:
                continue

            effective_date = str(
                effective_date
            )

            if effective_date <= as_of_date:

                filtered_documents.append(
                    document
                )

                filtered_metadatas.append(
                    metadata
                )

                filtered_distances.append(
                    distance
                )

        return (
            filtered_documents,
            filtered_metadatas,
            filtered_distances
        )

    # =============================================================
    # QUERY EMBEDDING
    # =============================================================

    def _embed_query(
        self,
        query: str
    ):

        tfidf = (
            self.vectorizer.transform(
                [query]
            )
        )

        embedding = (
            self.svd.transform(
                tfidf
            )
        )

        return embedding.astype(
            np.float32
        )

    # =============================================================
    # MAIN RETRIEVAL
    # =============================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        policy_id: Optional[str] = None,
        version_number: Optional[int] = None,
        category: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
        as_of_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:

        if (
            not query
            or not query.strip()
        ):

            return []

        # ---------------------------------------------------------
        # QUERY EMBEDDING
        # ---------------------------------------------------------

        query_embedding = (
            self._embed_query(
                query
            )
        )

        # ---------------------------------------------------------
        # CHROMA FILTER
        # ---------------------------------------------------------

        where_filter = (
            self._build_where_filter(
                policy_id=policy_id,
                version_number=version_number,
                category=category,
                department=department,
                status=status,
            )
        )

        # ---------------------------------------------------------
        # CANDIDATE COUNT
        # ---------------------------------------------------------
        #
        # We retrieve more candidates than top_k because the
        # intent-aware reranker needs a larger candidate pool.
        #
        # If an as_of_date is supplied, use an even larger pool
        # because some candidates may later be removed by the
        # date filter.
        # ---------------------------------------------------------

        if as_of_date:

            candidate_count = max(
                100,
                top_k * 20
            )

        else:

            candidate_count = max(
                50,
                top_k * 10
            )

        candidate_count = min(
            candidate_count,
            self.collection.count()
        )

        # ---------------------------------------------------------
        # CHROMA QUERY
        # ---------------------------------------------------------

        query_kwargs = {

            "query_embeddings":
                query_embedding.tolist(),

            "n_results":
                candidate_count,

            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        if where_filter:

            query_kwargs[
                "where"
            ] = where_filter

        results = (
            self.collection.query(
                **query_kwargs
            )
        )

        documents = (
            results["documents"][0]
        )

        metadatas = (
            results["metadatas"][0]
        )

        distances = (
            results["distances"][0]
        )

        if not documents:

            return []

        # ---------------------------------------------------------
        # VERSION-AWARE DATE FILTER
        # ---------------------------------------------------------

        (
            documents,
            metadatas,
            distances
        ) = self._filter_by_as_of_date(
            documents,
            metadatas,
            distances,
            as_of_date,
        )

        if not documents:

            return []

        # ---------------------------------------------------------
        # LEXICAL SIMILARITY
        # ---------------------------------------------------------

        lexical_scores = (
            self._lexical_similarity(
                query,
                documents
            )
        )

        # ---------------------------------------------------------
        # HYBRID + INTENT-AWARE RERANKING
        # ---------------------------------------------------------

        ranked = []

        for index, (
            document,
            metadata,
            distance
        ) in enumerate(
            zip(
                documents,
                metadatas,
                distances
            )
        ):

            # -----------------------------------------------------
            # SEMANTIC SCORE
            # -----------------------------------------------------

            semantic_score = max(
                0.0,
                min(
                    1.0,
                    1.0
                    - float(distance)
                )
            )

            # -----------------------------------------------------
            # LEXICAL SCORE
            # -----------------------------------------------------

            lexical_score = float(
                max(
                    0.0,
                    min(
                        1.0,
                        lexical_scores[index]
                    )
                )
            )

            # -----------------------------------------------------
            # TERM OVERLAP
            # -----------------------------------------------------

            overlap_score = (
                self._term_overlap(
                    query,
                    document
                )
            )

            # -----------------------------------------------------
            # SECTION INTENT
            # -----------------------------------------------------

            section_score = (
                self._section_relevance(
                    query,
                    metadata
                )
            )

            # -----------------------------------------------------
            # SUBJECT INTENT
            # -----------------------------------------------------

            subject_score = (
                self._subject_relevance(
                    query,
                    metadata,
                    document
                )
            )

            # -----------------------------------------------------
            # FINAL RERANK SCORE
            # -----------------------------------------------------
            #
            # Semantic      = 35%
            # Lexical       = 20%
            # Term overlap  = 10%
            # Section       = 20%
            # Subject       = 15%
            #
            # This preserves the hybrid retrieval architecture
            # while giving explicit user intent more influence.
            # -----------------------------------------------------

            final_score = (

                0.35
                * semantic_score

                + 0.20
                * lexical_score

                + 0.10
                * overlap_score

                + 0.20
                * section_score

                + 0.15
                * subject_score
            )

            ranked.append({

                "chunk_id":
                    metadata.get(
                        "chunk_id"
                    ),

                "policy_id":
                    metadata.get(
                        "policy_id"
                    ),

                "policy_name":
                    metadata.get(
                        "policy_name"
                    ),

                "category":
                    metadata.get(
                        "category"
                    ),

                "department":
                    metadata.get(
                        "department"
                    ),

                "version_number":
                    metadata.get(
                        "version_number"
                    ),

                "policy_version_id":
                    metadata.get(
                        "policy_version_id"
                    ),

                "effective_date":
                    metadata.get(
                        "effective_date"
                    ),

                "status":
                    metadata.get(
                        "status"
                    ),

                "section_index":
                    metadata.get(
                        "section_index"
                    ),

                "section_title":
                    metadata.get(
                        "section_title"
                    ),

                "file_path":
                    metadata.get(
                        "file_path"
                    ),

                "evidence":
                    document,

                # Original semantic similarity
                "similarity":
                    semantic_score,

                # Detailed scoring
                "semantic_score":
                    semantic_score,

                "lexical_score":
                    lexical_score,

                "term_overlap_score":
                    overlap_score,

                "section_score":
                    section_score,

                "subject_score":
                    subject_score,

                "rerank_score":
                    final_score,
            })

        # ---------------------------------------------------------
        # SORT
        # ---------------------------------------------------------

        ranked.sort(
            key=lambda x:
                x["rerank_score"],
            reverse=True
        )

        return ranked[:top_k]

    # =============================================================
    # RETRIEVE SPECIFIC POLICY
    # =============================================================

    def retrieve_policy(
        self,
        policy_id: str,
        query: str,
        top_k: int = 5,
        version_number: Optional[int] = None,
        as_of_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:

        return self.retrieve(

            query=query,

            top_k=top_k,

            policy_id=policy_id,

            version_number=version_number,

            as_of_date=as_of_date,
        )

    # =============================================================
    # RETRIEVE SPECIFIC POLICY VERSION
    # =============================================================

    def retrieve_policy_version(
        self,
        policy_id: str,
        version_number: int,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:

        return self.retrieve(

            query=query,

            top_k=top_k,

            policy_id=policy_id,

            version_number=version_number,
        )

    # =============================================================
    # RETRIEVE ACTIVE POLICY
    # =============================================================

    def retrieve_active_policy(
        self,
        policy_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:

        return self.retrieve(

            query=query,

            top_k=top_k,

            policy_id=policy_id,

            status="active",
        )


# =============================================================
# SINGLETON
# =============================================================

_policy_retrieval_service = None


def get_policy_retrieval_service():

    global _policy_retrieval_service

    if (
        _policy_retrieval_service
        is None
    ):

        _policy_retrieval_service = (
            PolicyRetrievalService()
        )

    return (
        _policy_retrieval_service
    )