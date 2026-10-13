from pathlib import Path
from typing import Optional, List, Dict, Any

import pickle
import numpy as np
import chromadb


# ============================================================
# POLICYLENS
# PHASE 2D - VERSION-AWARE LEGAL RETRIEVAL SERVICE
# ============================================================


class LegalRetrievalService:
    """
    PolicyLens Phase 2D

    Responsibilities:
        1. Load the Phase 2B TF-IDF vectorizer
        2. Load the Phase 2B SVD model
        3. Load the persistent ChromaDB legal collection
        4. Transform user queries into the same 384-D space
        5. Retrieve relevant legal evidence
        6. Apply version-aware filtering
        7. Return source metadata and evidence
    """

    COLLECTION_NAME = "policylens_legal"

    TOP_K_DEFAULT = 5

    # Retrieve more candidates internally so that
    # version filtering does not accidentally remove
    # all relevant results.
    CANDIDATE_K = 50

    def __init__(self):

        # ----------------------------------------------------
        # PROJECT PATHS
        # ----------------------------------------------------

        self.project_root = (
            Path(__file__).resolve().parents[3]
        )

        self.embedding_dir = (
            self.project_root
            / "data"
            / "processed"
            / "legal_rag"
            / "embeddings"
        )

        self.vectorstore_dir = (
            self.project_root
            / "data"
            / "vectorstore"
            / "legal_chroma"
        )

        self.vectorizer_path = (
            self.embedding_dir
            / "tfidf_vectorizer.pkl"
        )

        self.svd_path = (
            self.embedding_dir
            / "svd_model.pkl"
        )

        # ----------------------------------------------------
        # VALIDATE FILES
        # ----------------------------------------------------

        self._validate_paths()

        # ----------------------------------------------------
        # LOAD PHASE 2B MODELS
        # ----------------------------------------------------

        print(
            "Loading TF-IDF vectorizer..."
        )

        with open(
            self.vectorizer_path,
            "rb"
        ) as f:

            self.vectorizer = pickle.load(f)

        print(
            "TF-IDF vectorizer loaded."
        )

        print(
            "Loading SVD model..."
        )

        with open(
            self.svd_path,
            "rb"
        ) as f:

            self.svd_model = pickle.load(f)

        print(
            "SVD model loaded."
        )

        # ----------------------------------------------------
        # LOAD CHROMADB
        # ----------------------------------------------------

        print(
            "Loading persistent ChromaDB..."
        )

        self.chroma_client = (
            chromadb.PersistentClient(
                path=str(
                    self.vectorstore_dir
                )
            )
        )

        self.collection = (
            self.chroma_client.get_collection(
                name=self.COLLECTION_NAME
            )
        )

        print(
            "ChromaDB collection loaded."
        )

        print(
            f"Collection: "
            f"{self.COLLECTION_NAME}"
        )

        print(
            f"Records: "
            f"{self.collection.count():,}"
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def _validate_paths(self):

        required_paths = [
            self.vectorizer_path,
            self.svd_path,
            self.vectorstore_dir,
        ]

        for path in required_paths:

            if not path.exists():

                raise FileNotFoundError(
                    f"Required Phase 2D resource "
                    f"not found:\n{path}"
                )

    # ========================================================
    # QUERY EMBEDDING
    # ========================================================

    def _embed_query(
        self,
        query: str
    ) -> np.ndarray:

        if not query or not query.strip():

            raise ValueError(
                "Query cannot be empty."
            )

        query = query.strip()

        # Same TF-IDF transformation used
        # during Phase 2B.
        tfidf_vector = (
            self.vectorizer.transform(
                [query]
            )
        )

        # Same SVD projection used
        # during Phase 2B.
        embedding = (
            self.svd_model.transform(
                tfidf_vector
            )
        )

        # L2 normalization.
        norm = np.linalg.norm(
            embedding,
            axis=1,
            keepdims=True
        )

        norm[norm == 0] = 1.0

        embedding = (
            embedding / norm
        )

        return embedding[0]

    # ========================================================
    # DATE PARSING
    # ========================================================

    @staticmethod
    def _parse_date(
        value: Any
    ) -> Optional[str]:

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        # We normalize only the common
        # YYYY-MM-DD form here.
        #
        # Other formats are left unchanged
        # and handled conservatively.
        if len(value) >= 10:

            candidate = value[:10]

            parts = candidate.split("-")

            if (
                len(parts) == 3
                and all(
                    part.isdigit()
                    for part in parts
                )
            ):

                return candidate

        return None

    # ========================================================
    # VERSION FILTERING
    # ========================================================

    def _version_matches(
        self,
        metadata: Dict[str, Any],
        as_of_date: Optional[str]
    ) -> bool:

        if not as_of_date:
            return True

        effective_date = (
            self._parse_date(
                metadata.get(
                    "effective_date"
                )
            )
        )

        if not effective_date:
            return False

        # ISO YYYY-MM-DD strings sort correctly.
        return effective_date <= as_of_date

    # ========================================================
    # METADATA FILTERING
    # ========================================================

    def _metadata_matches(
        self,
        metadata: Dict[str, Any],
        act_title: Optional[str],
        document: Optional[str],
        version: Optional[str],
    ) -> bool:

        if act_title:

            stored_act = str(
                metadata.get(
                    "act_title",
                    ""
                )
            ).strip()

            if (
                stored_act.lower()
                != act_title.strip().lower()
            ):
                return False

        if document:

            stored_document = str(
                metadata.get(
                    "document",
                    ""
                )
            ).strip()

            if (
                stored_document.lower()
                != document.strip().lower()
            ):
                return False

        if version:

            stored_version = str(
                metadata.get(
                    "version_raw",
                    ""
                )
            ).strip()

            if (
                stored_version.lower()
                != version.strip().lower()
            ):
                return False

        return True

    # ========================================================
    # SOURCE METADATA
    # ========================================================

    @staticmethod
    def _build_source(
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {

            "chunk_id":
                metadata.get(
                    "chunk_id"
                ),

            "act_title":
                metadata.get(
                    "act_title"
                ),

            "document":
                metadata.get(
                    "document"
                ),

            "version":
                metadata.get(
                    "version_raw"
                ),

            "effective_date":
                metadata.get(
                    "effective_date"
                ),

            "category":
                metadata.get(
                    "category"
                ),

            "content_type":
                metadata.get(
                    "content_type"
                ),

            "source":
                metadata.get(
                    "source"
                ),

            "jurisdiction":
                metadata.get(
                    "jurisdiction"
                ),

            "file_path":
                metadata.get(
                    "file_path"
                ),

            "act_uri":
                metadata.get(
                    "act_uri"
                ),

            "chunk_index":
                metadata.get(
                    "chunk_index"
                ),

        }

    # ========================================================
    # EVIDENCE EXTRACTION
    # ========================================================

    @staticmethod
    def _build_evidence(
        rank: int,
        document: str,
        metadata: Dict[str, Any],
        distance: float
    ) -> Dict[str, Any]:

        # ChromaDB returns cosine distance.
        #
        # Smaller distance = more similar.
        #
        # Convert to a simple similarity score for
        # easier downstream use.
        similarity = max(
            0.0,
            1.0 - float(distance)
        )

        return {

            "rank": rank,

            "evidence_text": document,

            "similarity_score":
                round(
                    similarity,
                    6
                ),

            "distance":
                round(
                    float(distance),
                    6
                ),

            "source":
                LegalRetrievalService
                ._build_source(
                    metadata
                ),

        }

    # ========================================================
    # RETRIEVE
    # ========================================================

    def retrieve(
        self,
        query: str,
        top_k: int = TOP_K_DEFAULT,
        as_of_date: Optional[str] = None,
        act_title: Optional[str] = None,
        document: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:

        # ----------------------------------------------------
        # VALIDATE PARAMETERS
        # ----------------------------------------------------

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if as_of_date:

            parsed_date = (
                self._parse_date(
                    as_of_date
                )
            )

            if parsed_date is None:

                raise ValueError(
                    "as_of_date must use "
                    "YYYY-MM-DD format."
                )

            as_of_date = parsed_date

        # ----------------------------------------------------
        # CREATE QUERY VECTOR
        # ----------------------------------------------------

        query_vector = (
            self._embed_query(
                query
            )
        )

        # ----------------------------------------------------
        # CHROMADB SEARCH
        # ----------------------------------------------------

        result = self.collection.query(

            query_embeddings=[
                query_vector.tolist()
            ],

            n_results=self.CANDIDATE_K,

            include=[
                "documents",
                "metadatas",
                "distances",
            ],

        )

        candidate_ids = (
            result["ids"][0]
        )

        candidate_documents = (
            result["documents"][0]
        )

        candidate_metadatas = (
            result["metadatas"][0]
        )

        candidate_distances = (
            result["distances"][0]
        )

        # ----------------------------------------------------
        # FILTER + EVIDENCE EXTRACTION
        # ----------------------------------------------------

        evidence = []

        for index in range(
            len(candidate_ids)
        ):

            metadata = (
                candidate_metadatas[index]
            )

            legal_document = (
                candidate_documents[index]
            )

            distance = (
                candidate_distances[index]
            )

            # Explicit metadata filters
            if not self._metadata_matches(
                metadata=metadata,
                act_title=act_title,
                document=document,
                version=version,
            ):

                continue

            # Version-aware date filter
            if not self._version_matches(
                metadata=metadata,
                as_of_date=as_of_date,
            ):

                continue

            evidence_item = (
                self._build_evidence(
                    rank=len(evidence) + 1,
                    document=legal_document,
                    metadata=metadata,
                    distance=distance,
                )
            )

            evidence.append(
                evidence_item
            )

            if len(evidence) >= top_k:
                break

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {

            "query": query,

            "retrieval": {

                "top_k": top_k,

                "candidate_count":
                    len(candidate_ids),

                "returned_count":
                    len(evidence),

                "as_of_date":
                    as_of_date,

                "act_title":
                    act_title,

                "document":
                    document,

                "version":
                    version,

            },

            "evidence": evidence,

        }

    # ========================================================
    # CONVENIENCE METHOD
    # ========================================================

    def search(
        self,
        query: str,
        top_k: int = TOP_K_DEFAULT,
    ) -> List[Dict[str, Any]]:

        result = self.retrieve(
            query=query,
            top_k=top_k,
        )

        return result["evidence"]