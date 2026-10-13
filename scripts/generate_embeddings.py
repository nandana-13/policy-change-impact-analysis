import json
import os
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import save_npz


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASSAGES_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "passages.json"
)

EMBEDDINGS_DIR = os.path.join(
    BASE_DIR,
    "embeddings"
)

os.makedirs(EMBEDDINGS_DIR, exist_ok=True)


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
# LOAD PASSAGES
# ============================================================

print("Loading passages...")

with open(PASSAGES_PATH, "r", encoding="utf-8") as file:
    passages = json.load(file)

print(f"Total records loaded: {len(passages)}")


# ============================================================
# CLEAN PASSAGES
# ============================================================

clean_passages = []

for item in passages:

    document_id = item.get("document_id")
    passage_id = item.get("passage_id")
    text = item.get("text")

    if document_id is None:
        continue

    if passage_id is None:
        continue

    if not text:
        continue

    text = text.strip()

    if len(text) < 10:
        continue

    clean_passages.append({
        "document_id": document_id,
        "passage_id": str(passage_id),
        "text": text
    })


print(f"Valid passages: {len(clean_passages)}")


# ============================================================
# EXTRACT TEXT
# ============================================================

texts = [
    item["text"]
    for item in clean_passages
]


# ============================================================
# TF-IDF VECTORISATION
# ============================================================

print("Creating TF-IDF vectorizer...")

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    min_df=1,
    max_df=0.95,
    sublinear_tf=True
)


print("Generating TF-IDF matrix...")

tfidf_matrix = vectorizer.fit_transform(texts)


print("TF-IDF generation completed.")


# ============================================================
# SAVE VECTORISER
# ============================================================

joblib.dump(
    vectorizer,
    VECTORIZER_PATH
)


# ============================================================
# SAVE MATRIX
# ============================================================

save_npz(
    MATRIX_PATH,
    tfidf_matrix
)


# ============================================================
# SAVE METADATA
# ============================================================

metadata = []

for item in clean_passages:

    metadata.append({
        "document_id": item["document_id"],
        "passage_id": item["passage_id"],
        "text": item["text"]
    })


with open(
    METADATA_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("TF-IDF INDEX GENERATION COMPLETED")
print("=" * 60)

print(f"Passages       : {len(clean_passages)}")
print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
print(f"Matrix shape   : {tfidf_matrix.shape}")

print()
print(f"Vectorizer     : {VECTORIZER_PATH}")
print(f"Matrix         : {MATRIX_PATH}")
print(f"Metadata       : {METADATA_PATH}")