from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt


# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EDA_DIR = PROJECT_ROOT / "data" / "eda"

EDA_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# LOAD PROCESSED DATA
# ------------------------------------------------------------

with open(
    PROCESSED_DIR / "questions.json",
    "r",
    encoding="utf-8"
) as file:
    questions = json.load(file)

with open(
    PROCESSED_DIR / "passages.json",
    "r",
    encoding="utf-8"
) as file:
    passages = json.load(file)

with open(
    PROCESSED_DIR / "dataset_summary.json",
    "r",
    encoding="utf-8"
) as file:
    dataset_summary = json.load(file)


# ------------------------------------------------------------
# QUESTION DATAFRAME
# ------------------------------------------------------------

question_rows = []

for question in questions:

    question_text = question["question"]

    question_rows.append({
        "question_id": question["question_id"],
        "question": question_text,
        "group": question["group"],
        "split": question["split"],
        "passage_count": len(question["passages"]),
        "question_word_count": len(question_text.split())
    })

question_df = pd.DataFrame(question_rows)


# ------------------------------------------------------------
# PASSAGE DATAFRAME
# ------------------------------------------------------------

passage_rows = []

for passage in passages:

    text = passage["text"]

    passage_rows.append({
        "document_id": passage["document_id"],
        "passage_id": passage["passage_id"],
        "text": text,
        "word_count": len(text.split()),
        "character_count": len(text)
    })

passage_df = pd.DataFrame(passage_rows)


# ------------------------------------------------------------
# DOCUMENT SUMMARY
# ------------------------------------------------------------

document_df = (
    passage_df
    .groupby("document_id")
    .agg(
        passage_count=("passage_id", "count"),
        average_passage_words=("word_count", "mean"),
        total_words=("word_count", "sum")
    )
    .reset_index()
)


# ------------------------------------------------------------
# SAVE CSV FILES
# ------------------------------------------------------------

question_df.to_csv(
    EDA_DIR / "question_summary.csv",
    index=False
)

passage_df.to_csv(
    EDA_DIR / "passage_summary.csv",
    index=False
)

document_df.to_csv(
    EDA_DIR / "document_summary.csv",
    index=False
)


# ------------------------------------------------------------
# PRINT DATASET OVERVIEW
# ------------------------------------------------------------

print("\n========================================")
print("OBLIQA DATASET EDA")
print("========================================")

print("\nDataset Overview")
print("----------------------------")

print(
    f"Total questions: "
    f"{len(question_df)}"
)

print(
    f"Unique documents: "
    f"{passage_df['document_id'].nunique()}"
)

print(
    f"Unique passages: "
    f"{len(passage_df)}"
)

print(
    f"Total passage references: "
    f"{question_df['passage_count'].sum()}"
)


# ------------------------------------------------------------
# SPLIT DISTRIBUTION
# ------------------------------------------------------------

print("\nQuestions by Split")
print("----------------------------")

print(
    question_df["split"]
    .value_counts()
)


# ------------------------------------------------------------
# GROUP DISTRIBUTION
# ------------------------------------------------------------

print("\nQuestions by Group")
print("----------------------------")

print(
    question_df["group"]
    .value_counts()
    .sort_index()
)


# ------------------------------------------------------------
# QUESTION STATISTICS
# ------------------------------------------------------------

print("\nQuestion Statistics")
print("----------------------------")

print(
    question_df[
        [
            "question_word_count",
            "passage_count"
        ]
    ].describe()
)


# ------------------------------------------------------------
# PASSAGE STATISTICS
# ------------------------------------------------------------

print("\nPassage Statistics")
print("----------------------------")

print(
    passage_df[
        [
            "word_count",
            "character_count"
        ]
    ].describe()
)


# ------------------------------------------------------------
# 1. QUESTIONS BY SPLIT
# ------------------------------------------------------------

plt.figure(figsize=(8, 5))

question_df["split"].value_counts().plot(
    kind="bar"
)

plt.title("Questions by Dataset Split")
plt.xlabel("Dataset Split")
plt.ylabel("Number of Questions")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig(
    EDA_DIR / "01_questions_by_split.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# 2. QUESTION LENGTH DISTRIBUTION
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.hist(
    question_df["question_word_count"],
    bins=30
)

plt.title("Question Length Distribution")
plt.xlabel("Number of Words")
plt.ylabel("Frequency")
plt.tight_layout()

plt.savefig(
    EDA_DIR / "02_question_length_distribution.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# 3. PASSAGE LENGTH DISTRIBUTION
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.hist(
    passage_df["word_count"],
    bins=30
)

plt.title("Passage Length Distribution")
plt.xlabel("Number of Words")
plt.ylabel("Frequency")
plt.tight_layout()

plt.savefig(
    EDA_DIR / "03_passage_length_distribution.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# 4. QUESTIONS PER GROUP
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

question_df["group"].value_counts().sort_index().plot(
    kind="bar"
)

plt.title("Questions by Group")
plt.xlabel("Group")
plt.ylabel("Number of Questions")
plt.tight_layout()

plt.savefig(
    EDA_DIR / "04_questions_by_group.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# 5. PASSAGES PER DOCUMENT
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.hist(
    document_df["passage_count"],
    bins=20
)

plt.title("Passages per Regulatory Document")
plt.xlabel("Number of Passages")
plt.ylabel("Number of Documents")
plt.tight_layout()

plt.savefig(
    EDA_DIR / "05_passages_per_document.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# 6. PASSAGES PER QUESTION
# ------------------------------------------------------------

plt.figure(figsize=(8, 5))

question_df["passage_count"].value_counts().sort_index().plot(
    kind="bar"
)

plt.title("Passages per Question")
plt.xlabel("Number of Passages")
plt.ylabel("Number of Questions")
plt.tight_layout()

plt.savefig(
    EDA_DIR / "06_passages_per_question.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# 7. TOP REFERENCED DOCUMENTS
# ------------------------------------------------------------

document_reference_counts = (
    question_df
    .explode("passage_count")
)

document_counts = {}

for question in questions:

    for passage in question["passages"]:

        document_id = passage["document_id"]

        document_counts[document_id] = (
            document_counts.get(document_id, 0) + 1
        )

top_documents = (
    pd.Series(document_counts)
    .sort_values(ascending=False)
    .head(15)
)


plt.figure(figsize=(10, 6))

top_documents.plot(
    kind="bar"
)

plt.title("Top 15 Most Referenced Documents")
plt.xlabel("Document ID")
plt.ylabel("Number of References")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    EDA_DIR / "07_top_referenced_documents.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# COMPLETION
# ------------------------------------------------------------

print("\nEDA completed successfully.")

print("\nGenerated files:")
print(" - question_summary.csv")
print(" - passage_summary.csv")
print(" - document_summary.csv")
print(" - 01_questions_by_split.png")
print(" - 02_question_length_distribution.png")
print(" - 03_passage_length_distribution.png")
print(" - 04_questions_by_group.png")
print(" - 05_passages_per_document.png")
print(" - 06_passages_per_question.png")
print(" - 07_top_referenced_documents.png")