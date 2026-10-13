import os
import joblib

from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EMBEDDINGS_DIR = os.path.join(
    BASE_DIR,
    "embeddings"
)

VECTORIZER_PATH = os.path.join(
    EMBEDDINGS_DIR,
    "tfidf_vectorizer.joblib"
)

MATRIX_PATH = os.path.join(
    EMBEDDINGS_DIR,
    "tfidf_matrix.npz"
)

METADATA_PATH = os.path.join(
    EMBEDDINGS_DIR,
    "passage_metadata.json"
)


# ============================================================
# LOAD COMPONENTS
# ============================================================

print("Loading TF-IDF vectorizer...")

vectorizer = joblib.load(
    VECTORIZER_PATH
)

print("Loading TF-IDF matrix...")

tfidf_matrix = load_npz(
    MATRIX_PATH
)

print("Loading passage metadata...")

import json

with open(
    METADATA_PATH,
    "r",
    encoding="utf-8"
) as file:

    metadata = json.load(file)


print()
print(f"Loaded passages: {len(metadata)}")
print(f"Matrix shape: {tfidf_matrix.shape}")


# ============================================================
# GET USER QUERY
# ============================================================

query = input(
    "\nEnter your policy question: "
)


# ============================================================
# CONVERT QUERY TO TF-IDF
# ============================================================

query_vector = vectorizer.transform(
    [query]
)


# ============================================================
# CALCULATE SIMILARITY
# ============================================================

similarities = cosine_similarity(
    query_vector,
    tfidf_matrix
)[0]


# ============================================================
# GET TOP 5
# ============================================================

top_k = 5

top_indices = similarities.argsort()[-top_k:][::-1]


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("=" * 70)
print("TOP RETRIEVED PASSAGES")
print("=" * 70)


for rank, index in enumerate(
    top_indices,
    start=1
):

    item = metadata[index]

    print()
    print(f"Rank          : {rank}")
    print(f"Document ID   : {item['document_id']}")
    print(f"Passage ID    : {item['passage_id']}")
    print(f"Similarity    : {similarities[index]:.4f}")

    print()
    print("Text:")
    print(item["text"])

    print("-" * 70)