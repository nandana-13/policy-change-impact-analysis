from pathlib import Path
import json
import time
import pickle

import numpy as np
import pandas as pd

from tqdm import tqdm

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize


class LegalEmbeddingService:

    """
    PolicyLens Phase 2B

    Local legal retrieval representation using:

        TF-IDF
          +
        Truncated SVD / LSA

    No external embedding API.
    No Hugging Face model.
    No transformer download.

    The resulting vectors are used later for:

        ChromaDB
            ↓
        Legal Retrieval
            ↓
        Explainable RAG
    """

    # ---------------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------------

    EMBEDDING_DIMENSION = 384

    MIN_DF = 2

    MAX_DF = 0.95

    MAX_FEATURES = 50000

    RANDOM_STATE = 42

    # ---------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------

    def __init__(self):

        print("=" * 70)
        print("POLICYLENS - LOCAL LEGAL EMBEDDING SERVICE")
        print("=" * 70)

        print("\nEmbedding approach:")
        print("TF-IDF + Truncated SVD / LSA")

        print(
            f"\nTarget embedding dimension: "
            f"{self.EMBEDDING_DIMENSION}"
        )

        print(
            f"Maximum vocabulary size: "
            f"{self.MAX_FEATURES:,}"
        )

    # ---------------------------------------------------------------
    # Validate input
    # ---------------------------------------------------------------

    def _validate_input(self, df):

        required_columns = [
            "chunk_id",
            "doc_type",
            "category",
            "document",
            "version_raw",
            "chunk_index",
            "text",
            "file_path",
            "act_title",
            "act_uri",
            "source",
            "jurisdiction",
            "content_type",
            "effective_date"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:

            raise ValueError(
                "Missing required columns: "
                f"{missing_columns}"
            )

        # -----------------------------------------------------------
        # Empty corpus
        # -----------------------------------------------------------

        if len(df) == 0:

            raise ValueError(
                "Legal corpus is empty."
            )

        # -----------------------------------------------------------
        # Duplicate chunk IDs
        # -----------------------------------------------------------

        duplicate_count = (
            df["chunk_id"]
            .duplicated()
            .sum()
        )

        if duplicate_count > 0:

            raise ValueError(
                f"Found {duplicate_count} "
                "duplicate chunk IDs."
            )

        # -----------------------------------------------------------
        # Missing text
        # -----------------------------------------------------------

        missing_text = (
            df["text"]
            .isna()
            .sum()
        )

        if missing_text > 0:

            raise ValueError(
                f"Found {missing_text} "
                "chunks with missing text."
            )

        # -----------------------------------------------------------
        # Empty text
        # -----------------------------------------------------------

        empty_text = (
            df["text"]
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )

        if empty_text > 0:

            raise ValueError(
                f"Found {empty_text} "
                "chunks with empty text."
            )

        print("\nInput validation passed.")

    # ---------------------------------------------------------------
    # Generate local embeddings
    # ---------------------------------------------------------------

    def generate_embeddings(
        self,
        input_file: Path,
        output_directory: Path
    ):

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        # -----------------------------------------------------------
        # Load Phase 2A corpus
        # -----------------------------------------------------------

        print("\nLoading legal corpus...")

        df = pd.read_parquet(
            input_file
        )

        print(
            f"Total legal chunks: "
            f"{len(df):,}"
        )

        self._validate_input(df)

        # Keep deterministic ordering
        df = df.reset_index(
            drop=True
        )

        texts = (
            df["text"]
            .astype(str)
            .tolist()
        )

        total_chunks = len(texts)

        # -----------------------------------------------------------
        # Output paths
        # -----------------------------------------------------------

        embeddings_file = (
            output_directory /
            "embeddings.npy"
        )

        metadata_file = (
            output_directory /
            "embedding_metadata.parquet"
        )

        vectorizer_file = (
            output_directory /
            "tfidf_vectorizer.pkl"
        )

        svd_file = (
            output_directory /
            "svd_model.pkl"
        )

        manifest_file = (
            output_directory /
            "embedding_manifest.json"
        )

        # -----------------------------------------------------------
        # TF-IDF
        # -----------------------------------------------------------

        print("\n" + "=" * 70)
        print("STEP 1 - TF-IDF")
        print("=" * 70)

        print(
            "\nBuilding legal vocabulary..."
        )

        vectorizer = TfidfVectorizer(

            lowercase=True,

            strip_accents="unicode",

            stop_words="english",

            ngram_range=(1, 2),

            min_df=self.MIN_DF,

            max_df=self.MAX_DF,

            max_features=self.MAX_FEATURES,

            sublinear_tf=True
        )

        start_time = time.time()

        tfidf_matrix = (
            vectorizer.fit_transform(
                texts
            )
        )

        tfidf_time = (
            time.time() - start_time
        )

        vocabulary_size = (
            len(vectorizer.vocabulary_)
        )

        print(
            f"\nVocabulary size:"
            f" {vocabulary_size:,}"
        )

        print(
            f"TF-IDF matrix shape:"
            f" {tfidf_matrix.shape}"
        )

        print(
            f"TF-IDF generation time:"
            f" {tfidf_time / 60:.2f} minutes"
        )

        # -----------------------------------------------------------
        # Verify vocabulary
        # -----------------------------------------------------------

        if vocabulary_size == 0:

            raise ValueError(
                "TF-IDF vocabulary is empty."
            )

        # -----------------------------------------------------------
        # Determine valid SVD dimensions
        # -----------------------------------------------------------

        max_svd_dimension = min(
            self.EMBEDDING_DIMENSION,
            tfidf_matrix.shape[0] - 1,
            tfidf_matrix.shape[1] - 1
        )

        if max_svd_dimension < 2:

            raise ValueError(
                "Corpus is too small for "
                "Truncated SVD."
            )

        # -----------------------------------------------------------
        # Truncated SVD / LSA
        # -----------------------------------------------------------

        print("\n" + "=" * 70)
        print("STEP 2 - TRUNCATED SVD / LSA")
        print("=" * 70)

        print(
            f"\nRequested dimensions:"
            f" {self.EMBEDDING_DIMENSION}"
        )

        print(
            f"Actual dimensions:"
            f" {max_svd_dimension}"
        )

        svd = TruncatedSVD(

            n_components=max_svd_dimension,

            random_state=self.RANDOM_STATE
        )

        start_time = time.time()

        dense_embeddings = (
            svd.fit_transform(
                tfidf_matrix
            )
        )

        svd_time = (
            time.time() - start_time
        )

        # -----------------------------------------------------------
        # Normalize vectors
        # -----------------------------------------------------------

        dense_embeddings = normalize(
            dense_embeddings,
            norm="l2"
        )

        dense_embeddings = np.asarray(
            dense_embeddings,
            dtype=np.float32
        )

        print(
            f"\nEmbedding matrix:"
            f" {dense_embeddings.shape}"
        )

        print(
            f"SVD generation time:"
            f" {svd_time / 60:.2f} minutes"
        )

        # -----------------------------------------------------------
        # Explained variance
        # -----------------------------------------------------------

        explained_variance = float(
            svd.explained_variance_ratio_.sum()
        )

        print(
            f"\nExplained variance:"
            f" {explained_variance:.4f}"
        )

        print(
            f"Explained variance:"
            f" {explained_variance * 100:.2f}%"
        )

        # -----------------------------------------------------------
        # Validate embeddings
        # -----------------------------------------------------------

        if dense_embeddings.shape[0] != total_chunks:

            raise ValueError(
                "Embedding count does not match "
                "legal chunk count."
            )

        if not np.isfinite(
            dense_embeddings
        ).all():

            raise ValueError(
                "Embedding matrix contains "
                "NaN or infinite values."
            )

        # -----------------------------------------------------------
        # Save embeddings
        # -----------------------------------------------------------

        print("\n" + "=" * 70)
        print("STEP 3 - SAVING EMBEDDINGS")
        print("=" * 70)

        np.save(
            embeddings_file,
            dense_embeddings
        )

        print(
            f"\nEmbeddings saved:"
            f"\n{embeddings_file}"
        )

        # -----------------------------------------------------------
        # Save metadata
        # -----------------------------------------------------------

        metadata_columns = [

            "chunk_id",

            "doc_type",

            "category",

            "document",

            "version_raw",

            "effective_date",

            "chunk_index",

            "file_path",

            "act_title",

            "act_uri",

            "source",

            "jurisdiction",

            "content_type"
        ]

        metadata = df[
            metadata_columns
        ].copy()

        metadata.to_parquet(
            metadata_file,
            index=False
        )

        print(
            f"\nMetadata saved:"
            f"\n{metadata_file}"
        )

        # -----------------------------------------------------------
        # Save TF-IDF model
        # -----------------------------------------------------------

        with open(
            vectorizer_file,
            "wb"
        ) as f:

            pickle.dump(
                vectorizer,
                f
            )

        print(
            f"\nTF-IDF vectorizer saved:"
            f"\n{vectorizer_file}"
        )

        # -----------------------------------------------------------
        # Save SVD model
        # -----------------------------------------------------------

        with open(
            svd_file,
            "wb"
        ) as f:

            pickle.dump(
                svd,
                f
            )

        print(
            f"\nSVD model saved:"
            f"\n{svd_file}"
        )

        # -----------------------------------------------------------
        # Save manifest
        # -----------------------------------------------------------

        manifest = {

            "project": "PolicyLens",

            "component": "legal_rag",

            "phase": "2B",

            "status": "completed",

            "purpose": (
                "Generate fully local legal retrieval "
                "vectors for PolicyLens Explainable RAG."
            ),

            "embedding_method": {

                "type": (
                    "TF-IDF + Truncated SVD / "
                    "Latent Semantic Analysis"
                ),

                "provider": "local",

                "external_api": False,

                "huggingface_required": False,

                "dimension":
                    int(
                        dense_embeddings.shape[1]
                    ),

                "normalized": True
            },

            "tfidf": {

                "vocabulary_size":
                    vocabulary_size,

                "min_df":
                    self.MIN_DF,

                "max_df":
                    self.MAX_DF,

                "max_features":
                    self.MAX_FEATURES,

                "ngram_range": [
                    1,
                    2
                ]
            },

            "svd": {

                "components":
                    int(
                        dense_embeddings.shape[1]
                    ),

                "random_state":
                    self.RANDOM_STATE,

                "explained_variance":
                    explained_variance
            },

            "source": {

                "input_file":
                    str(input_file),

                "total_legal_chunks":
                    total_chunks
            },

            "outputs": {

                "embeddings":
                    str(embeddings_file),

                "metadata":
                    str(metadata_file),

                "tfidf_vectorizer":
                    str(vectorizer_file),

                "svd_model":
                    str(svd_file)
            },

            "next_phase":
                "2C - ChromaDB vector indexing"
        }

        with open(
            manifest_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                manifest,
                f,
                indent=2
            )

        # -----------------------------------------------------------
        # Final validation
        # -----------------------------------------------------------

        print("\n" + "=" * 70)
        print("PHASE 2B VALIDATION")
        print("=" * 70)

        print(
            f"\nExpected legal chunks:"
            f" {total_chunks:,}"
        )

        print(
            f"Generated vectors:"
            f" {dense_embeddings.shape[0]:,}"
        )

        print(
            f"Vector dimension:"
            f" {dense_embeddings.shape[1]}"
        )

        print(
            f"Vocabulary:"
            f" {vocabulary_size:,}"
        )

        print(
            f"Explained variance:"
            f" {explained_variance * 100:.2f}%"
        )

        print(
            "\nMethod:"
            " Local TF-IDF + SVD"
        )

        print(
            "\nExternal API:"
            " None"
        )

        print(
            "\nHugging Face:"
            " Not required"
        )

        print("\n" + "=" * 70)
        print("PHASE 2B SUCCESS")
        print("=" * 70)

        print(
            "\nAll legal chunks have been "
            "converted into local retrieval vectors."
        )

        print(
            "\nReady for Phase 2C: ChromaDB."
        )

        return {

            "total_chunks":
                total_chunks,

            "total_embeddings":
                dense_embeddings.shape[0],

            "dimension":
                dense_embeddings.shape[1],

            "vocabulary_size":
                vocabulary_size,

            "explained_variance":
                explained_variance,

            "method":
                "TF-IDF + Truncated SVD / LSA"
        }