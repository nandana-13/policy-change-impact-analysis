from functools import lru_cache
from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

PROCESSED_CORPUS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "legal_rag"
)

PROCESSED_CHUNKS_FILE = (
    PROCESSED_CORPUS_DIR
    / "legal_chunks.parquet"
)

MANIFEST_FILE = (
    PROCESSED_CORPUS_DIR
    / "corpus_manifest.json"
)


@lru_cache(maxsize=1)
def load_legal_corpus() -> pd.DataFrame:
    """
    Load the processed legal corpus once and keep it in memory.
    """

    if not PROCESSED_CHUNKS_FILE.exists():
        raise FileNotFoundError(
            "Processed legal corpus does not exist. "
            "Run backend/prepare_legal_corpus.py first."
        )

    return pd.read_parquet(
        PROCESSED_CHUNKS_FILE
    )


def get_manifest() -> dict:
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            "Legal corpus manifest does not exist. "
            "Run backend/prepare_legal_corpus.py first."
        )

    with open(
        MANIFEST_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def get_stats() -> dict:
    df = load_legal_corpus()

    return {
        "total_chunks": int(len(df)),
        "total_acts": int(
            df["category"].nunique()
        ),
        "total_documents": int(
            df["document"].nunique()
        ),
                "total_point_in_time_versions": int(
            df[
                [
                    "document",
                    "version_raw",
                ]
            ]
            .drop_duplicates()
            .shape[0]
        ),
        "unique_version_dates": int(
            df["version_raw"].nunique()
        ),
        "total_chunk_ids": int(
            df["chunk_id"].nunique()
        ),
        "acts": sorted(
            df["category"]
            .dropna()
            .unique()
            .tolist()
        ),
        "documents": sorted(
            df["document"]
            .dropna()
            .unique()
            .tolist()
        ),
        "version_dates": sorted(
            df["version_raw"]
            .dropna()
            .unique()
            .tolist()
        ),
    }


def get_status() -> dict:
    manifest = get_manifest()

    statistics = manifest["statistics"]

    return {
        "status": manifest["status"],
        "phase": manifest["phase"],
        "total_chunks": statistics["total_chunks"],
        "embeddings_status": manifest[
            "embedding_status"
        ],
        "vector_database_status": manifest[
            "vector_database_status"
        ],
    }


def get_sources() -> list[dict]:
    df = load_legal_corpus()

    grouped = (
        df.groupby(
            [
                "category",
                "act_title",
            ],
            dropna=False,
        )
        .agg(
            chunk_count=(
                "chunk_id",
                "count",
            ),
            document_count=(
                "document",
                "nunique",
            ),
            version_count=(
                "version_raw",
                "nunique",
            ),
            earliest_version=(
                "version_raw",
                "min",
            ),
            latest_version=(
                "version_raw",
                "max",
            ),
        )
        .reset_index()
    )

    return grouped.to_dict(
        orient="records"
    )