from pathlib import Path
import json
import time

import chromadb
import numpy as np
import pandas as pd


# ============================================================
# POLICYLENS
# PHASE 2C - LEGAL CHROMADB
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LEGAL_RAG_DIR = PROJECT_ROOT / "data" / "processed" / "legal_rag"

EMBEDDING_DIR = LEGAL_RAG_DIR / "embeddings"

LEGAL_CHUNKS_FILE = LEGAL_RAG_DIR / "legal_chunks.parquet"
EMBEDDINGS_FILE = EMBEDDING_DIR / "embeddings.npy"
EMBEDDING_METADATA_FILE = EMBEDDING_DIR / "embedding_metadata.parquet"

VECTORSTORE_DIR = (
    PROJECT_ROOT
    / "data"
    / "vectorstore"
    / "legal_chroma"
)

MANIFEST_FILE = VECTORSTORE_DIR / "chromadb_manifest.json"

COLLECTION_NAME = "policylens_legal"

BATCH_SIZE = 1000


# ============================================================
# UTILITY
# ============================================================

def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# VALIDATE INPUT FILES
# ============================================================

def validate_input_files():

    print_header("INPUT VALIDATION")

    required_files = [
        LEGAL_CHUNKS_FILE,
        EMBEDDINGS_FILE,
        EMBEDDING_METADATA_FILE,
    ]

    for file_path in required_files:

        print(f"Checking: {file_path}")

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found:\n{file_path}"
            )

        print("  OK")

    print("\nAll required Phase 2B files are available.")


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print_header("LOADING PHASE 2B DATA")

    print("Loading embeddings...")
    embeddings = np.load(EMBEDDINGS_FILE)

    print(f"Embeddings shape: {embeddings.shape}")

    print("\nLoading embedding metadata...")
    metadata = pd.read_parquet(EMBEDDING_METADATA_FILE)

    print(f"Metadata rows: {len(metadata)}")

    print("\nLoading legal chunks...")
    chunks = pd.read_parquet(LEGAL_CHUNKS_FILE)

    print(f"Legal chunk rows: {len(chunks)}")

    return embeddings, metadata, chunks


# ============================================================
# VALIDATE DATA CONSISTENCY
# ============================================================

def validate_data(embeddings, metadata, chunks):

    print_header("DATA CONSISTENCY VALIDATION")

    embedding_count = embeddings.shape[0]
    metadata_count = len(metadata)
    chunk_count = len(chunks)

    print(f"Embedding vectors : {embedding_count:,}")
    print(f"Metadata records   : {metadata_count:,}")
    print(f"Legal chunks       : {chunk_count:,}")

    if embedding_count != metadata_count:
        raise ValueError(
            "Embedding count does not match metadata count."
        )

    if embedding_count != chunk_count:
        raise ValueError(
            "Embedding count does not match legal chunk count."
        )

    if "chunk_id" not in metadata.columns:
        raise ValueError(
            "embedding_metadata.parquet does not contain chunk_id."
        )

    if "chunk_id" not in chunks.columns:
        raise ValueError(
            "legal_chunks.parquet does not contain chunk_id."
        )

    if "text" not in chunks.columns:
        raise ValueError(
            "legal_chunks.parquet does not contain text."
        )

    metadata_ids = set(metadata["chunk_id"])
    chunk_ids = set(chunks["chunk_id"])

    if metadata_ids != chunk_ids:
        missing_from_chunks = metadata_ids - chunk_ids
        missing_from_metadata = chunk_ids - metadata_ids

        raise ValueError(
            "chunk_id mismatch detected.\n"
            f"Missing from chunks: {len(missing_from_chunks)}\n"
            f"Missing from metadata: {len(missing_from_metadata)}"
        )

    if not np.isfinite(embeddings).all():
        raise ValueError(
            "Embeddings contain NaN or infinite values."
        )

    print("\nData consistency validation PASSED.")


# ============================================================
# PREPARE DOCUMENT DATA
# ============================================================

def prepare_documents(metadata, chunks):

    print_header("PREPARING CHROMADB DOCUMENTS")

    # Only use chunk_id + text from original legal corpus.
    # This guarantees that ChromaDB stores the actual legal evidence.
    text_lookup = (
        chunks[["chunk_id", "text"]]
        .drop_duplicates("chunk_id")
        .set_index("chunk_id")["text"]
        .to_dict()
    )

    documents = []

    for chunk_id in metadata["chunk_id"]:

        text = text_lookup.get(chunk_id)

        if text is None:
            raise ValueError(
                f"Legal text not found for chunk_id: {chunk_id}"
            )

        text = str(text).strip()

        if not text:
            raise ValueError(
                f"Empty legal text for chunk_id: {chunk_id}"
            )

        documents.append(text)

    print(f"Prepared documents: {len(documents):,}")

    return documents


# ============================================================
# PREPARE CHROMADB METADATA
# ============================================================

def clean_metadata_value(value):

    if pd.isna(value):
        return ""

    return str(value)


def prepare_metadata(metadata):

    print_header("PREPARING CHROMADB METADATA")

    chroma_metadata = []

    for _, row in metadata.iterrows():

        item = {
            "chunk_id": clean_metadata_value(
                row.get("chunk_id", "")
            ),

            "doc_type": clean_metadata_value(
                row.get("doc_type", "")
            ),

            "category": clean_metadata_value(
                row.get("category", "")
            ),

            "document": clean_metadata_value(
                row.get("document", "")
            ),

            "version_raw": clean_metadata_value(
                row.get("version_raw", "")
            ),

            "effective_date": clean_metadata_value(
                row.get("effective_date", "")
            ),

            "chunk_index": clean_metadata_value(
                row.get("chunk_index", "")
            ),

            "file_path": clean_metadata_value(
                row.get("file_path", "")
            ),

            "act_title": clean_metadata_value(
                row.get("act_title", "")
            ),

            "act_uri": clean_metadata_value(
                row.get("act_uri", "")
            ),

            "source": clean_metadata_value(
                row.get("source", "")
            ),

            "jurisdiction": clean_metadata_value(
                row.get("jurisdiction", "")
            ),

            "content_type": clean_metadata_value(
                row.get("content_type", "")
            ),
        }

        chroma_metadata.append(item)

    print(
        f"Prepared metadata records: "
        f"{len(chroma_metadata):,}"
    )

    return chroma_metadata


# ============================================================
# CREATE CHROMADB
# ============================================================

def create_chromadb(
    embeddings,
    metadata,
    documents
):

    print_header("CREATING CHROMADB")

    VECTORSTORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print(f"Persistent database:")
    print(VECTORSTORE_DIR)

    print("\nInitializing ChromaDB...")

    client = chromadb.PersistentClient(
        path=str(VECTORSTORE_DIR)
    )

    # --------------------------------------------------------
    # Remove previous collection if it exists.
    #
    # This makes the script safely reproducible and prevents
    # duplicate/stale records when Phase 2C is rerun.
    # --------------------------------------------------------

    try:

        client.delete_collection(
            name=COLLECTION_NAME
        )

        print(
            f"Existing collection '{COLLECTION_NAME}' "
            f"deleted."
        )

    except Exception:
        print(
            f"No existing collection '{COLLECTION_NAME}' "
            f"found. Creating new collection."
        )

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": (
                "PolicyLens legal knowledge base"
            ),
            "project": "PolicyLens",
            "phase": "2C",
            "source": "UK Legal Corpus",
            "embedding_method": "TF-IDF + SVD",
            "embedding_dimension": 384,
            "distance_metric": "cosine",
        },
        configuration={
            "hnsw": {
                "space": "cosine"
            }
        }
    )

    print(
        f"Collection created: {COLLECTION_NAME}"
    )

    # --------------------------------------------------------
    # ADD DATA IN BATCHES
    # --------------------------------------------------------

    total = len(metadata)

    start_time = time.time()

    for start in range(0, total, BATCH_SIZE):

        end = min(
            start + BATCH_SIZE,
            total
        )

        batch_metadata = metadata[start:end]

        batch_documents = documents[start:end]

        batch_embeddings = embeddings[start:end]

        batch_ids = [
            str(item["chunk_id"])
            for item in batch_metadata
        ]

        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings.tolist(),
            documents=batch_documents,
            metadatas=batch_metadata,
        )

        print(
            f"Inserted "
            f"{end:,}/{total:,} "
            f"records"
        )

    elapsed = time.time() - start_time

    print()
    print(
        f"ChromaDB insertion time: "
        f"{elapsed / 60:.2f} minutes"
    )

    return client, collection


# ============================================================
# VALIDATE CHROMADB
# ============================================================

def validate_chromadb(
    collection,
    embeddings,
    metadata,
    documents
):

    print_header("CHROMADB VALIDATION")

    count = collection.count()

    print(
        f"Expected records : {len(metadata):,}"
    )

    print(
        f"ChromaDB records : {count:,}"
    )

    if count != len(metadata):
        raise ValueError(
            "ChromaDB record count does not match "
            "expected record count."
        )

    print("\nRecord count validation PASSED.")

    # --------------------------------------------------------
    # Retrieve one known vector.
    #
    # This validates:
    # - vector storage
    # - metadata storage
    # - document storage
    # - similarity search
    # --------------------------------------------------------

    test_index = 0

    test_embedding = embeddings[
        test_index
    ].tolist()

    test_chunk_id = str(
        metadata.iloc[test_index]["chunk_id"]
    )

    print()
    print("Running similarity-search validation...")

    result = collection.query(
        query_embeddings=[test_embedding],
        n_results=5,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    result_ids = result["ids"][0]

    print(
        f"Test chunk ID: {test_chunk_id}"
    )

    print("\nTop 5 retrieved chunks:")

    for rank, chunk_id in enumerate(
        result_ids,
        start=1
    ):

        distance = result["distances"][0][rank - 1]

        result_metadata = (
            result["metadatas"][0][rank - 1]
        )

        print(
            f"{rank}. "
            f"{chunk_id} | "
            f"{result_metadata.get('act_title', '')} | "
            f"distance={distance:.6f}"
        )

    if test_chunk_id not in result_ids:
        raise ValueError(
            "Similarity validation failed: "
            "test chunk was not retrieved."
        )

    print(
        "\nSimilarity-search validation PASSED."
    )

    # --------------------------------------------------------
    # Verify document + metadata
    # --------------------------------------------------------

    retrieved_document = (
        result["documents"][0][0]
    )

    retrieved_metadata = (
        result["metadatas"][0][0]
    )

    if not retrieved_document:
        raise ValueError(
            "Retrieved document text is empty."
        )

    required_metadata = [
        "chunk_id",
        "document",
        "version_raw",
        "effective_date",
        "act_title",
        "source",
        "jurisdiction",
    ]

    for field in required_metadata:

        if field not in retrieved_metadata:

            raise ValueError(
                f"Required metadata missing: {field}"
            )

    print(
        "Document storage validation PASSED."
    )

    print(
        "Metadata storage validation PASSED."
    )


# ============================================================
# SAVE MANIFEST
# ============================================================

def save_manifest(
    collection,
    embeddings,
    metadata
):

    print_header("SAVING CHROMADB MANIFEST")

    manifest = {

        "project": "PolicyLens",

        "component": "legal_rag",

        "phase": "2C",

        "status": "ready_for_retrieval",

        "vector_database": {

            "type": "ChromaDB",

            "collection": COLLECTION_NAME,

            "persistent": True,

            "path": str(
                VECTORSTORE_DIR
            ),

            "distance_metric": "cosine",

            "total_records": int(
                collection.count()
            ),

            "embedding_dimension": int(
                embeddings.shape[1]
            ),

        },

        "source": {

            "dataset":
                "Version-Aware RAG - UK Legal Corpus",

            "publisher":
                "Kajaluxan",

            "source_website":
                "legislation.gov.uk",

            "license":
                "Open Government Licence v3.0",

        },

        "statistics": {

            "total_chunks":
                int(len(metadata)),

            "total_vectors":
                int(embeddings.shape[0]),

            "vector_dimension":
                int(embeddings.shape[1]),

        },

        "metadata_fields": [

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
            "content_type",

        ],

        "embedding_method":
            "TF-IDF + Truncated SVD / LSA",

        "next_phase":
            "2D - Version-aware semantic retrieval",

    }

    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            manifest,
            f,
            indent=2
        )

    print(
        f"Manifest saved:\n{MANIFEST_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print_header(
        "POLICYLENS\n"
        "PHASE 2C - CHROMADB LEGAL VECTOR DATABASE"
    )

    print(
        "Purpose:"
    )

    print(
        "Create a persistent ChromaDB collection "
        "from the Phase 2B legal vectors."
    )

    print(
        "\nEmbedding generation will NOT be repeated."
    )

    # Step 1
    validate_input_files()

    # Step 2
    embeddings, metadata, chunks = load_data()

    # Step 3
    validate_data(
        embeddings,
        metadata,
        chunks
    )

    # Step 4
    documents = prepare_documents(
        metadata,
        chunks
    )

    # Step 5
    chroma_metadata = prepare_metadata(
        metadata
    )

    # Step 6
    client, collection = create_chromadb(
        embeddings,
        chroma_metadata,
        documents
    )

    # Step 7
    validate_chromadb(
        collection,
        embeddings,
        metadata,
        documents
    )

    # Step 8
    save_manifest(
        collection,
        embeddings,
        metadata
    )

    # Final
    print_header(
        "PHASE 2C SUCCESS"
    )

    print(
        "Legal ChromaDB has been created successfully."
    )

    print(
        f"\nCollection:"
        f" {COLLECTION_NAME}"
    )

    print(
        f"Records:"
        f" {collection.count():,}"
    )

    print(
        f"Vector dimension:"
        f" {embeddings.shape[1]}"
    )

    print(
        f"\nVector database:"
        f"\n{VECTORSTORE_DIR}"
    )

    print(
        "\nReady for Phase 2D:"
    )

    print(
        "Version-aware semantic retrieval"
    )


if __name__ == "__main__":
    main()