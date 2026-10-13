from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_CORPUS_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "version-aware-RAG-legal"
)

RAW_CHUNKS_FILE = (
    RAW_CORPUS_DIR
    / "chunks"
    / "chunks.parquet"
)

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


# ============================================================
# EXPECTED DATASET STRUCTURE
# ============================================================

REQUIRED_COLUMNS = [
    "chunk_id",
    "doc_type",
    "category",
    "document",
    "version_raw",
    "chunk_index",
    "text",
    "file_path",
]


# ============================================================
# ACT METADATA
# ============================================================

ACT_METADATA = {
    "data_protection_act_2018": {
        "title": "Data Protection Act 2018",
        "uri": "ukpga/2018/12",
    },
    "equality_act_2010": {
        "title": "Equality Act 2010",
        "uri": "ukpga/2010/15",
    },
    "finance_act_2003": {
        "title": "Finance Act 2003",
        "uri": "ukpga/2003/14",
    },
    "income_tax_earnings_pensions_act_2003": {
        "title": "Income Tax (Earnings and Pensions) Act 2003",
        "uri": "ukpga/2003/1",
    },
    "localism_act_2011": {
        "title": "Localism Act 2011",
        "uri": "ukpga/2011/20",
    },
}


# ============================================================
# FILE VALIDATION
# ============================================================

def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Required corpus file was not found:\n{path}"
        )


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Legal corpus is missing required columns: "
            + ", ".join(missing)
        )


def _validate_values(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError(
            "Legal corpus contains zero rows."
        )

    if df["chunk_id"].isna().any():
        raise ValueError(
            "chunk_id contains missing values."
        )

    if df["text"].isna().any():
        raise ValueError(
            "text contains missing values."
        )

    if df["category"].isna().any():
        raise ValueError(
            "category contains missing values."
        )

    if df["document"].isna().any():
        raise ValueError(
            "document contains missing values."
        )

    if df["version_raw"].isna().any():
        raise ValueError(
            "version_raw contains missing values."
        )

    duplicate_count = df["chunk_id"].duplicated().sum()

    if duplicate_count > 0:
        raise ValueError(
            f"Found {duplicate_count} duplicate chunk_id values."
        )


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_corpus(
    df: pd.DataFrame,
) -> pd.DataFrame:

    normalized = df.copy()

    # Normalize text fields.
    text_columns = [
        "chunk_id",
        "doc_type",
        "category",
        "document",
        "version_raw",
        "text",
        "file_path",
    ]

    for column in text_columns:
        normalized[column] = (
            normalized[column]
            .astype("string")
            .str.strip()
        )

    # Normalize chunk index.
    normalized["chunk_index"] = pd.to_numeric(
        normalized["chunk_index"],
        errors="raise",
    ).astype("int64")

    # Normalize effective date.
    normalized["effective_date"] = pd.to_datetime(
        normalized["version_raw"],
        errors="raise",
    ).dt.strftime("%Y-%m-%d")

    # Add friendly Act title.
    normalized["act_title"] = normalized[
        "category"
    ].map(
        lambda category: ACT_METADATA.get(
            category,
            {},
        ).get(
            "title",
            category.replace("_", " ").title(),
        )
    )

    # Add legislation URI.
    normalized["act_uri"] = normalized[
        "category"
    ].map(
        lambda category: ACT_METADATA.get(
            category,
            {},
        ).get("uri")
    )

    # Source information.
    normalized["source"] = (
        "legislation.gov.uk"
    )

    normalized["jurisdiction"] = (
        "United Kingdom"
    )

    normalized["content_type"] = "legal"

    # Consistent column order.
    ordered_columns = [
        "chunk_id",
        "content_type",
        "doc_type",
        "category",
        "act_title",
        "act_uri",
        "document",
        "version_raw",
        "effective_date",
        "chunk_index",
        "text",
        "file_path",
        "source",
        "jurisdiction",
    ]

    return normalized[ordered_columns]


# ============================================================
# STATISTICS
# ============================================================

def build_statistics(
    df: pd.DataFrame,
) -> dict:

    acts = sorted(
        df["category"]
        .dropna()
        .unique()
        .tolist()
    )

    documents = sorted(
        df["document"]
        .dropna()
        .unique()
        .tolist()
    )

    version_dates = sorted(
        df["version_raw"]
        .dropna()
        .unique()
        .tolist()
    )

    # A point-in-time version belongs to a specific
    # document/Part AND a specific version date.
    #
    # Therefore:
    #
    # document + version_raw
    #
    # represents one point-in-time version.
    point_in_time_versions = (
        df[
            [
                "document",
                "version_raw",
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )

    return {
        "total_chunks": int(
            len(df)
        ),

        "total_acts": int(
            df["category"].nunique()
        ),

        "total_documents": int(
            df["document"].nunique()
        ),

        "total_point_in_time_versions": int(
            point_in_time_versions
        ),

        "unique_version_dates": int(
            len(version_dates)
        ),

        "total_chunk_ids": int(
            df["chunk_id"].nunique()
        ),

        "acts": acts,

        "documents": documents,

        "version_dates": version_dates,
    }


# ============================================================
# MAIN PROCESSOR
# ============================================================

def process_legal_corpus() -> dict:

    print("=" * 70)
    print(
        "POLICYLENS - LEGAL CORPUS PROCESSOR"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Locate raw corpus
    # --------------------------------------------------------

    print("\nRaw corpus:")
    print(RAW_CHUNKS_FILE)

    _require_file(
        RAW_CHUNKS_FILE
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print("\nLoading parquet...")

    df = pd.read_parquet(
        RAW_CHUNKS_FILE
    )

    print(
        f"Rows loaded: {len(df):,}"
    )

    print(
        f"Columns found: {len(df.columns)}"
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    print("\nValidating columns...")

    _validate_columns(df)

    print(
        "✓ Required columns present"
    )

    print("\nValidating values...")

    _validate_values(df)

    print(
        "✓ No missing critical values"
    )

    print(
        "✓ No duplicate chunk IDs"
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    print("\nNormalizing corpus...")

    normalized_df = normalize_corpus(
        df
    )

    print(
        "✓ Metadata normalized"
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    statistics = build_statistics(
        normalized_df
    )

    print("\nCorpus statistics")
    print("-" * 40)

    print(
        f"Total chunks            : "
        f"{statistics['total_chunks']:,}"
    )

    print(
        f"Total Acts              : "
        f"{statistics['total_acts']}"
    )

    print(
        f"Total documents         : "
        f"{statistics['total_documents']}"
    )

    print(
        f"Point-in-time versions  : "
        f"{statistics['total_point_in_time_versions']}"
    )

    print(
        f"Unique version dates    : "
        f"{statistics['unique_version_dates']}"
    )

    # --------------------------------------------------------
    # Act-level statistics
    # --------------------------------------------------------

    print("\nActs:")

    for act in statistics["acts"]:

        title = ACT_METADATA.get(
            act,
            {},
        ).get(
            "title",
            act,
        )

        count = int(
            (
                normalized_df["category"]
                == act
            ).sum()
        )

        print(
            f"  - {title}: "
            f"{count:,} chunks"
        )

    # --------------------------------------------------------
    # Expected dataset validation
    # --------------------------------------------------------

    expected_chunks = 18_935
    expected_documents = 96
    expected_versions = 355

    if (
        statistics["total_chunks"]
        != expected_chunks
    ):
        raise ValueError(
            f"Expected {expected_chunks:,} chunks, "
            f"but found "
            f"{statistics['total_chunks']:,}."
        )

    if (
        statistics["total_documents"]
        != expected_documents
    ):
        raise ValueError(
            f"Expected {expected_documents} documents, "
            f"but found "
            f"{statistics['total_documents']}."
        )

    if (
        statistics[
            "total_point_in_time_versions"
        ]
        != expected_versions
    ):
        raise ValueError(
            f"Expected {expected_versions} "
            f"point-in-time versions, "
            f"but found "
            f"{statistics['total_point_in_time_versions']}."
        )

    print(
        f"\n✓ Chunk count matches expected "
        f"{expected_chunks:,}"
    )

    print(
        f"✓ Document count matches expected "
        f"{expected_documents}"
    )

    print(
        f"✓ Point-in-time version count "
        f"matches expected {expected_versions}"
    )

    print(
        f"✓ Unique version dates: "
        f"{statistics['unique_version_dates']}"
    )

    # --------------------------------------------------------
    # Create processed directory
    # --------------------------------------------------------

    PROCESSED_CORPUS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Save processed corpus
    # --------------------------------------------------------

    print(
        "\nWriting processed corpus..."
    )

    normalized_df.to_parquet(
        PROCESSED_CHUNKS_FILE,
        index=False,
    )

    print(
        f"✓ Saved:\n"
        f"{PROCESSED_CHUNKS_FILE}"
    )

    # --------------------------------------------------------
    # Create manifest
    # --------------------------------------------------------

    processed_at = datetime.now(
        timezone.utc
    ).isoformat()

    manifest = {
        "project": "PolicyLens",

        "component": "legal_rag",

        "phase": "2A",

        "status": "ready_for_embedding",

        "source": {
            "dataset": (
                "Version-Aware RAG - "
                "UK Legal Corpus"
            ),
            "publisher": "Kajaluxan",
            "source_website": (
                "legislation.gov.uk"
            ),
            "license": (
                "Open Government "
                "Licence v3.0"
            ),
        },

        "raw_file": str(
            RAW_CHUNKS_FILE
            .relative_to(PROJECT_ROOT)
        ),

        "processed_file": str(
            PROCESSED_CHUNKS_FILE
            .relative_to(PROJECT_ROOT)
        ),

        "statistics": statistics,

        "required_columns": (
            REQUIRED_COLUMNS
        ),

        "processed_columns": (
            normalized_df.columns.tolist()
        ),

        "processed_at": processed_at,

        "embedding_status": (
            "not_started"
        ),

        "vector_database_status": (
            "not_started"
        ),
    }

    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            manifest,
            file,
            indent=2,
        )

    print(
        f"✓ Manifest saved:\n"
        f"{MANIFEST_FILE}"
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PHASE 2A COMPLETE")
    print("=" * 70)

    print(
        "\nLegal corpus is validated and ready "
        "for Phase 2B embedding generation."
    )

    return manifest


if __name__ == "__main__":
    process_legal_corpus()