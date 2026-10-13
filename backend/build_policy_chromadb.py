from pathlib import Path
import json
import re
import pickle
import time

import chromadb
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD


# ============================================================
# POLICYLENS
# PHASE 2E - COMPANY POLICY RETRIEVAL
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "PolicyLens_dataset_upgraded"
)

DOCUMENTS_DIR = DATA_DIR / "documents"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "policy_rag"
)

EMBEDDING_DIR = OUTPUT_DIR / "embeddings"

VECTORSTORE_DIR = (
    PROJECT_ROOT
    / "data"
    / "vectorstore"
    / "policy_chroma"
)

POLICIES_FILE = DATA_DIR / "policies_upgraded.json"
VERSIONS_FILE = DATA_DIR / "policy_versions_upgraded.json"

COLLECTION_NAME = "policylens_policies"

BATCH_SIZE = 500

EMBEDDING_DIMENSION = 384

MAX_FEATURES = 50000


# ============================================================
# HELPERS
# ============================================================

def print_header(title):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def clean_text(text):

    text = str(text)

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive whitespace while
    # preserving paragraph boundaries.
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# ============================================================
# VALIDATE INPUTS
# ============================================================

def validate_inputs():

    print_header("INPUT VALIDATION")

    required_paths = [
        DATA_DIR,
        DOCUMENTS_DIR,
        POLICIES_FILE,
        VERSIONS_FILE,
    ]

    for path in required_paths:

        print(f"Checking: {path}")

        if not path.exists():

            raise FileNotFoundError(
                f"Required path not found:\n{path}"
            )

        print("  OK")

    print(
        "\nCompany policy dataset "
        "is available."
    )


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# NORMALIZE JSON STRUCTURE
# ============================================================

def normalize_records(data):

    if isinstance(data, list):

        return data

    if isinstance(data, dict):

        for key in [
            "policies",
            "policy_versions",
            "data",
            "records",
            "items",
        ]:

            if key in data:

                value = data[key]

                if isinstance(value, list):

                    return value

    raise ValueError(
        "Unsupported JSON structure."
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_dataset():

    print_header("LOADING COMPANY POLICY DATA")

    policies_data = load_json(
        POLICIES_FILE
    )

    versions_data = load_json(
        VERSIONS_FILE
    )

    policies = normalize_records(
        policies_data
    )

    versions = normalize_records(
        versions_data
    )

    print(
        f"Policies loaded : {len(policies):,}"
    )

    print(
        f"Versions loaded : {len(versions):,}"
    )

    return policies, versions


# ============================================================
# CREATE LOOKUPS
# ============================================================

def create_policy_lookup(policies):

    lookup = {}

    for policy in policies:

        policy_id = str(
            policy.get(
                "policy_id",
                ""
            )
        ).strip()

        if not policy_id:
            continue

        lookup[policy_id] = policy

    return lookup


# ============================================================
# DOCUMENT DISCOVERY
# ============================================================

def find_policy_document(
    policy_id,
    version_number
):

    version_dir = (
        DOCUMENTS_DIR
        / policy_id
        / f"V{version_number}"
    )

    candidates = [
        version_dir / "policy.md",
        version_dir / "policy.txt",
    ]

    for candidate in candidates:

        if candidate.exists():

            return candidate

    # Fallback recursive search.
    if version_dir.exists():

        files = list(
            version_dir.glob("*")
        )

        for file_path in files:

            if file_path.is_file():

                return file_path

    return None


# ============================================================
# SECTION EXTRACTION
# ============================================================

def extract_sections(
    text
):

    """
    Extract Markdown-style sections.

    Expected generated policy structure:

        # Policy Name
        ## 1. Purpose
        ## 2. Scope
        ## 3. Definitions
        ## 4. Policy Requirements
        ...

    Each section becomes an independent
    retrieval unit.
    """

    text = clean_text(text)

    lines = text.split("\n")

    sections = []

    current_title = "Document Introduction"

    current_lines = []

    for line in lines:

        stripped = line.strip()

        # Markdown heading.
        if stripped.startswith("#"):

            if current_lines:

                section_text = clean_text(
                    "\n".join(
                        current_lines
                    )
                )

                if section_text:

                    sections.append(
                        {
                            "section_title":
                                current_title,
                            "text":
                                section_text,
                        }
                    )

            current_title = (
                stripped
                .lstrip("#")
                .strip()
            )

            current_lines = []

        else:

            current_lines.append(
                line
            )

    # Final section.
    if current_lines:

        section_text = clean_text(
            "\n".join(
                current_lines
            )
        )

        if section_text:

            sections.append(
                {
                    "section_title":
                        current_title,
                    "text":
                        section_text,
                }
            )

    return sections


# ============================================================
# BUILD POLICY CHUNKS
# ============================================================

def build_policy_chunks(
    policies,
    versions
):

    print_header(
        "BUILDING COMPANY POLICY RETRIEVAL CHUNKS"
    )

    policy_lookup = (
        create_policy_lookup(
            policies
        )
    )

    records = []

    missing_documents = []

    for version in versions:

        policy_id = str(
            version.get(
                "policy_id",
                ""
            )
        ).strip()

        version_number = int(
            version.get(
                "version_number"
            )
        )

        policy = policy_lookup.get(
            policy_id,
            {}
        )

        document_path = (
            find_policy_document(
                policy_id,
                version_number
            )
        )

        if document_path is None:

            missing_documents.append(
                f"{policy_id}-V{version_number}"
            )

            continue

        with open(
            document_path,
            "r",
            encoding="utf-8"
        ) as f:

            text = f.read()

        sections = extract_sections(
            text
        )

        for section_index, section in enumerate(
            sections
        ):

            section_text = section[
                "text"
            ]

            if not section_text.strip():
                continue

            chunk_id = (
                f"{policy_id}"
                f"-V{version_number}"
                f"-S{section_index + 1:02d}"
            )

            # Context is deliberately included
            # in the indexed text so that retrieval
            # understands which policy/version the
            # section belongs to.
            indexed_text = (
                f"Policy: "
                f"{policy.get('policy_name', policy_id)}\n"
                f"Policy ID: {policy_id}\n"
                f"Category: "
                f"{policy.get('category', '')}\n"
                f"Department: "
                f"{policy.get('department', '')}\n"
                f"Version: V{version_number}\n"
                f"Section: "
                f"{section['section_title']}\n\n"
                f"{section_text}"
            )

            records.append(
                {
                    "chunk_id":
                        chunk_id,

                    "policy_id":
                        policy_id,

                    "policy_name":
                        str(
                            policy.get(
                                "policy_name",
                                ""
                            )
                        ),

                    "category":
                        str(
                            policy.get(
                                "category",
                                ""
                            )
                        ),

                    "department":
                        str(
                            policy.get(
                                "department",
                                ""
                            )
                        ),

                    "version_number":
                        version_number,

                    "policy_version_id":
                        str(
                            version.get(
                                "policy_version_id",
                                ""
                            )
                        ),

                    "effective_date":
                        str(
                            version.get(
                                "effective_date",
                                ""
                            )
                        ),

                    "status":
                        str(
                            version.get(
                                "status",
                                ""
                            )
                        ),

                    "change_description":
                        str(
                            version.get(
                                "change_description",
                                ""
                            )
                        ),

                    "section_index":
                        section_index + 1,

                    "section_title":
                        section[
                            "section_title"
                        ],

                    "file_path":
                        str(
                            document_path
                        ),

                    "text":
                        section_text,

                    "indexed_text":
                        indexed_text,
                }
            )

    if missing_documents:

        print(
            "\nWARNING:"
        )

        print(
            "Missing policy documents:"
        )

        for item in missing_documents:

            print(
                f"  {item}"
            )

    print(
        f"\nGenerated policy sections: "
        f"{len(records):,}"
    )

    if not records:

        raise RuntimeError(
            "No policy retrieval chunks "
            "were generated."
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# SAVE CHUNKS
# ============================================================

def save_chunks(df):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        OUTPUT_DIR
        / "policy_chunks.parquet"
    )

    df.to_parquet(
        output_file,
        index=False
    )

    print(
        f"Policy chunks saved:\n"
        f"{output_file}"
    )


# ============================================================
# GENERATE EMBEDDINGS
# ============================================================

def generate_embeddings(df):

    print_header(
        "GENERATING COMPANY POLICY EMBEDDINGS"
    )

    texts = (
        df["indexed_text"]
        .astype(str)
        .tolist()
    )

    print(
        f"Input policy sections: "
        f"{len(texts):,}"
    )

    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    print(
        "\nSTEP 1 - TF-IDF"
    )

    vectorizer = TfidfVectorizer(

        lowercase=True,

        strip_accents="unicode",

        stop_words="english",

        ngram_range=(1, 2),

        min_df=1,

        max_df=0.98,

        max_features=MAX_FEATURES,

        sublinear_tf=True,

    )

    start = time.time()

    tfidf_matrix = (
        vectorizer.fit_transform(
            texts
        )
    )

    elapsed = time.time() - start

    print(
        f"Vocabulary size: "
        f"{len(vectorizer.vocabulary_):,}"
    )

    print(
        f"TF-IDF matrix shape: "
        f"{tfidf_matrix.shape}"
    )

    print(
        f"TF-IDF generation time: "
        f"{elapsed / 60:.2f} minutes"
    )

    # --------------------------------------------------------
    # SVD
    # --------------------------------------------------------

    print(
        "\nSTEP 2 - TRUNCATED SVD / LSA"
    )

    # The number of SVD components cannot
    # exceed min(samples - 1, features).
    max_components = min(
        tfidf_matrix.shape[0] - 1,
        tfidf_matrix.shape[1]
    )

    n_components = min(
        EMBEDDING_DIMENSION,
        max_components
    )

    print(
        f"Requested dimensions: "
        f"{EMBEDDING_DIMENSION}"
    )

    print(
        f"Actual dimensions: "
        f"{n_components}"
    )

    svd = TruncatedSVD(
        n_components=n_components,
        random_state=42
    )

    start = time.time()

    embeddings = svd.fit_transform(
        tfidf_matrix
    )

    elapsed = time.time() - start

    # L2 normalization.
    norms = np.linalg.norm(
        embeddings,
        axis=1,
        keepdims=True
    )

    norms[norms == 0] = 1.0

    embeddings = (
        embeddings / norms
    )

    print(
        f"Embedding matrix: "
        f"{embeddings.shape}"
    )

    print(
        f"SVD generation time: "
        f"{elapsed / 60:.2f} minutes"
    )

    print(
        f"Explained variance: "
        f"{svd.explained_variance_ratio_.sum():.4f}"
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    EMBEDDING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    embeddings_file = (
        EMBEDDING_DIR
        / "embeddings.npy"
    )

    metadata_file = (
        EMBEDDING_DIR
        / "embedding_metadata.parquet"
    )

    vectorizer_file = (
        EMBEDDING_DIR
        / "tfidf_vectorizer.pkl"
    )

    svd_file = (
        EMBEDDING_DIR
        / "svd_model.pkl"
    )

    np.save(
        embeddings_file,
        embeddings
    )

    metadata_columns = [
        "chunk_id",
        "policy_id",
        "policy_name",
        "category",
        "department",
        "version_number",
        "policy_version_id",
        "effective_date",
        "status",
        "change_description",
        "section_index",
        "section_title",
        "file_path",
        "text",
    ]

    df[
        metadata_columns
    ].to_parquet(
        metadata_file,
        index=False
    )

    with open(
        vectorizer_file,
        "wb"
    ) as f:

        pickle.dump(
            vectorizer,
            f
        )

    with open(
        svd_file,
        "wb"
    ) as f:

        pickle.dump(
            svd,
            f
        )

    print(
        "\nEmbeddings saved:"
    )

    print(
        embeddings_file
    )

    print(
        "\nMetadata saved:"
    )

    print(
        metadata_file
    )

    print(
        "\nTF-IDF vectorizer saved:"
    )

    print(
        vectorizer_file
    )

    print(
        "\nSVD model saved:"
    )

    print(
        svd_file
    )

    return (
        embeddings,
        df[
            metadata_columns
        ],
        vectorizer,
        svd,
    )


# ============================================================
# BUILD CHROMADB
# ============================================================

def build_chromadb(
    embeddings,
    metadata
):

    print_header(
        "BUILDING COMPANY POLICY CHROMADB"
    )

    VECTORSTORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=str(
            VECTORSTORE_DIR
        )
    )

    # Rebuild safely if rerun.
    try:

        client.delete_collection(
            name=COLLECTION_NAME
        )

        print(
            f"Existing collection "
            f"'{COLLECTION_NAME}' deleted."
        )

    except Exception:

        print(
            f"No existing collection "
            f"'{COLLECTION_NAME}' found."
        )

    collection = client.create_collection(

        name=COLLECTION_NAME,

        metadata={
            "description":
                "PolicyLens company policy knowledge base",

            "project":
                "PolicyLens",

            "phase":
                "2E",

            "embedding_method":
                "TF-IDF + SVD",

            "embedding_dimension":
                int(
                    embeddings.shape[1]
                ),

            "distance_metric":
                "cosine",
        },

        configuration={
            "hnsw": {
                "space": "cosine"
            }
        },
    )

    print(
        f"Collection created: "
        f"{COLLECTION_NAME}"
    )

    total = len(metadata)

    start_time = time.time()

    for start in range(
        0,
        total,
        BATCH_SIZE
    ):

        end = min(
            start + BATCH_SIZE,
            total
        )

        batch = metadata.iloc[
            start:end
        ]

        ids = (
            batch["chunk_id"]
            .astype(str)
            .tolist()
        )

        documents = (
            batch["text"]
            .astype(str)
            .tolist()
        )

        metadatas = []

        for _, row in batch.iterrows():

            metadatas.append(
                {
                    "chunk_id":
                        str(
                            row["chunk_id"]
                        ),

                    "policy_id":
                        str(
                            row["policy_id"]
                        ),

                    "policy_name":
                        str(
                            row["policy_name"]
                        ),

                    "category":
                        str(
                            row["category"]
                        ),

                    "department":
                        str(
                            row["department"]
                        ),

                    "version_number":
                        int(
                            row["version_number"]
                        ),

                    "policy_version_id":
                        str(
                            row["policy_version_id"]
                        ),

                    "effective_date":
                        str(
                            row["effective_date"]
                        ),

                    "status":
                        str(
                            row["status"]
                        ),

                    "section_index":
                        int(
                            row["section_index"]
                        ),

                    "section_title":
                        str(
                            row["section_title"]
                        ),

                    "file_path":
                        str(
                            row["file_path"]
                        ),
                }
            )

        collection.add(

            ids=ids,

            embeddings=(
                embeddings[start:end]
                .tolist()
            ),

            documents=documents,

            metadatas=metadatas,
        )

        print(
            f"Inserted "
            f"{end:,}/{total:,} policy sections"
        )

    elapsed = time.time() - start_time

    print(
        f"\nChromaDB insertion time: "
        f"{elapsed / 60:.2f} minutes"
    )

    return client, collection


# ============================================================
# VALIDATE
# ============================================================

def validate_chromadb(
    collection,
    embeddings,
    metadata
):

    print_header(
        "COMPANY POLICY CHROMADB VALIDATION"
    )

    expected = len(metadata)

    actual = collection.count()

    print(
        f"Expected records : "
        f"{expected:,}"
    )

    print(
        f"ChromaDB records : "
        f"{actual:,}"
    )

    if actual != expected:

        raise RuntimeError(
            "ChromaDB count mismatch."
        )

    print(
        "\nRecord count validation PASSED."
    )

    # --------------------------------------------------------
    # Similarity search
    # --------------------------------------------------------

    test_index = 0

    query_vector = (
        embeddings[test_index]
        .tolist()
    )

    result = collection.query(

        query_embeddings=[
            query_vector
        ],

        n_results=5,

        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    print(
        "\nTop 5 policy retrieval results:"
    )

    for rank in range(5):

        metadata_item = (
            result["metadatas"][0][rank]
        )

        distance = (
            result["distances"][0][rank]
        )

        print(
            f"\n{rank + 1}. "
            f"{metadata_item['policy_id']} | "
            f"{metadata_item['policy_name']} | "
            f"V{metadata_item['version_number']} | "
            f"{metadata_item['section_title']} | "
            f"distance={distance:.6f}"
        )

        print(
            result["documents"][0][rank][:250]
        )

    # Exact vector should retrieve itself.
    expected_id = str(
        metadata.iloc[
            test_index
        ]["chunk_id"]
    )

    returned_ids = (
        result["ids"][0]
    )

    if expected_id not in returned_ids:

        raise RuntimeError(
            "Similarity search validation failed."
        )

    print(
        "\nSimilarity-search validation PASSED."
    )


# ============================================================
# MANIFEST
# ============================================================

def save_manifest(
    collection,
    embeddings,
    metadata
):

    manifest = {

        "project":
            "PolicyLens",

        "component":
            "company_policy_rag",

        "phase":
            "2E",

        "status":
            "ready_for_policy_retrieval",

        "vector_database": {

            "type":
                "ChromaDB",

            "collection":
                COLLECTION_NAME,

            "path":
                str(
                    VECTORSTORE_DIR
                ),

            "distance_metric":
                "cosine",

            "total_records":
                int(
                    collection.count()
                ),

            "embedding_dimension":
                int(
                    embeddings.shape[1]
                ),
        },

        "statistics": {

            "total_policies":
                int(
                    metadata[
                        "policy_id"
                    ].nunique()
                ),

            "total_policy_versions":
                int(
                    metadata[
                        "policy_version_id"
                    ].nunique()
                ),

            "total_sections":
                int(
                    len(metadata)
                ),
        },

        "embedding_method":
            "TF-IDF + Truncated SVD / LSA",

        "metadata_fields": [

            "chunk_id",
            "policy_id",
            "policy_name",
            "category",
            "department",
            "version_number",
            "policy_version_id",
            "effective_date",
            "status",
            "section_index",
            "section_title",
            "file_path",

        ],

        "next_phase":
            "Policy retrieval service and integration",

    }

    manifest_file = (
        VECTORSTORE_DIR
        / "chromadb_manifest.json"
    )

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

    print(
        f"\nManifest saved:\n"
        f"{manifest_file}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print_header(
        "POLICYLENS\n"
        "PHASE 2E - COMPANY POLICY RETRIEVAL"
    )

    print(
        "Company policies will be indexed "
        "in a separate ChromaDB."
    )

    print(
        "The legal ChromaDB will NOT be modified."
    )

    # --------------------------------------------------------
    # 1. Validate
    # --------------------------------------------------------

    validate_inputs()

    # --------------------------------------------------------
    # 2. Load
    # --------------------------------------------------------

    policies, versions = (
        load_dataset()
    )

    # --------------------------------------------------------
    # 3. Build chunks
    # --------------------------------------------------------

    chunks_df = (
        build_policy_chunks(
            policies,
            versions
        )
    )

    # --------------------------------------------------------
    # 4. Save chunks
    # --------------------------------------------------------

    save_chunks(
        chunks_df
    )

    # --------------------------------------------------------
    # 5. Embeddings
    # --------------------------------------------------------

    (
        embeddings,
        metadata,
        vectorizer,
        svd,
    ) = generate_embeddings(
        chunks_df
    )

    # --------------------------------------------------------
    # 6. ChromaDB
    # --------------------------------------------------------

    client, collection = (
        build_chromadb(
            embeddings,
            metadata
        )
    )

    # --------------------------------------------------------
    # 7. Validate
    # --------------------------------------------------------

    validate_chromadb(
        collection,
        embeddings,
        metadata
    )

    # --------------------------------------------------------
    # 8. Manifest
    # --------------------------------------------------------

    save_manifest(
        collection,
        embeddings,
        metadata
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print_header(
        "PHASE 2E SUCCESS"
    )

    print(
        "Company policy retrieval "
        "knowledge base created successfully."
    )

    print(
        f"\nPolicies: "
        f"{metadata['policy_id'].nunique():,}"
    )

    print(
        f"Versions: "
        f"{metadata['policy_version_id'].nunique():,}"
    )

    print(
        f"Sections: "
        f"{len(metadata):,}"
    )

    print(
        f"Vector dimension: "
        f"{embeddings.shape[1]}"
    )

    print(
        f"\nChromaDB:"
        f"\n{VECTORSTORE_DIR}"
    )

    print(
        "\nLegal ChromaDB remains untouched."
    )


if __name__ == "__main__":
    main()