import json
import numpy as np
from pathlib import Path
from joblib import load
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

QUESTIONS_FILE = BASE_DIR / "data" / "processed" / "questions.json"
VECTORIZER_FILE = BASE_DIR / "embeddings" / "tfidf_vectorizer.joblib"
MATRIX_FILE = BASE_DIR / "embeddings" / "tfidf_matrix.npz"
METADATA_FILE = BASE_DIR / "embeddings" / "passage_metadata.json"


TOP_K_VALUES = [1, 3, 5, 10]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("LOADING RETRIEVAL DATA")
print("=" * 70)

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

vectorizer = load(VECTORIZER_FILE)
tfidf_matrix = load_npz(MATRIX_FILE)

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"Questions loaded : {len(questions)}")
print(f"Passages loaded  : {len(metadata)}")
print(f"Matrix shape     : {tfidf_matrix.shape}")


# ============================================================
# PREPARE METADATA
# ============================================================

passage_keys = []

for item in metadata:
    document_id = str(item["document_id"])
    passage_id = str(item["passage_id"])

    passage_keys.append((document_id, passage_id))


# ============================================================
# INITIALIZE SPLIT STATISTICS
# ============================================================

stats = {}

for split in ["train", "dev", "test"]:
    stats[split] = {
        "total": 0,
        "hits": {
            1: 0,
            3: 0,
            5: 0,
            10: 0
        }
    }


# ============================================================
# EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("RUNNING SPLIT-WISE RETRIEVAL EVALUATION")
print("=" * 70)

for index, question_data in enumerate(questions):

    question = question_data["question"]
    split = question_data.get("split", "unknown")

    # Ignore unexpected splits
    if split not in stats:
        continue

    stats[split]["total"] += 1

    # --------------------------------------------------------
    # Expected passages
    # --------------------------------------------------------

    expected_passages = set()

    for passage in question_data.get("passages", []):

        document_id = str(passage["document_id"])
        passage_id = str(passage["passage_id"])

        expected_passages.add(
            (document_id, passage_id)
        )

    if not expected_passages:
        continue

    # --------------------------------------------------------
    # Convert question into TF-IDF vector
    # --------------------------------------------------------

    query_vector = vectorizer.transform([question])

    # --------------------------------------------------------
    # Calculate cosine similarity
    # --------------------------------------------------------

    similarities = cosine_similarity(
        query_vector,
        tfidf_matrix
    )[0]

    # --------------------------------------------------------
    # Rank passages
    # --------------------------------------------------------

    ranked_indices = np.argsort(
        similarities
    )[::-1]

    # --------------------------------------------------------
    # Calculate Recall@K
    # --------------------------------------------------------

    for k in TOP_K_VALUES:

        top_indices = ranked_indices[:k]

        retrieved_passages = set(
            passage_keys[i]
            for i in top_indices
        )

        # Hit if at least one expected passage is retrieved
        if expected_passages & retrieved_passages:
            stats[split]["hits"][k] += 1

    # Progress indicator
    if (index + 1) % 5000 == 0:
        print(
            f"Processed {index + 1}/{len(questions)} questions..."
        )


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("SPLIT-WISE RETRIEVAL RESULTS")
print("=" * 70)

for split in ["train", "dev", "test"]:

    total = stats[split]["total"]

    print(f"\n{split.upper()}")
    print("-" * 70)
    print(f"Questions : {total}")

    if total == 0:
        continue

    for k in TOP_K_VALUES:

        hits = stats[split]["hits"][k]

        recall = hits / total

        print(
            f"Recall@{k:<2} : "
            f"{recall:.4f} "
            f"({recall * 100:.2f}%)"
        )


# ============================================================
# OVERALL RESULTS
# ============================================================

print("\n" + "=" * 70)
print("OVERALL RESULTS")
print("=" * 70)

overall_total = sum(
    stats[split]["total"]
    for split in stats
)

print(f"Total questions : {overall_total}")

for k in TOP_K_VALUES:

    overall_hits = sum(
        stats[split]["hits"][k]
        for split in stats
    )

    recall = overall_hits / overall_total

    print(
        f"Recall@{k:<2} : "
        f"{recall:.4f} "
        f"({recall * 100:.2f}%)"
    )

print("\n" + "=" * 70)
print("EVALUATION COMPLETED")
print("=" * 70)