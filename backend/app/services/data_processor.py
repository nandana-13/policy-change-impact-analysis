from pathlib import Path
import json
from collections import Counter


# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "ObliQADataset-main"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# LOAD JSON FILE
# ------------------------------------------------------------

def load_json(file_name):
    file_path = DATASET_DIR / file_name

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ------------------------------------------------------------
# PROCESS QUESTIONS
# ------------------------------------------------------------

def process_questions(datasets):
    questions = []

    for split_name, records in datasets.items():

        for record in records:

            passages = []

            for passage in record.get("Passages", []):
                passages.append({
                    "document_id": passage.get("DocumentID"),
                    "passage_id": passage.get("PassageID"),
                    "text": passage.get("Passage", "").strip()
                })

            questions.append({
                "question_id": record.get("QuestionID"),
                "question": record.get("Question", "").strip(),
                "group": record.get("Group"),
                "split": split_name,
                "passages": passages
            })

    return questions


# ------------------------------------------------------------
# EXTRACT UNIQUE PASSAGES
# ------------------------------------------------------------

def extract_passages(questions):

    passage_dict = {}

    for question in questions:

        for passage in question["passages"]:

            key = (
                passage["document_id"],
                passage["passage_id"]
            )

            if key not in passage_dict:

                passage_dict[key] = {
                    "document_id": passage["document_id"],
                    "passage_id": passage["passage_id"],
                    "text": passage["text"]
                }

    return list(passage_dict.values())


# ------------------------------------------------------------
# DATASET SUMMARY
# ------------------------------------------------------------

def create_summary(datasets, questions, passages):

    split_counts = {
        split: len(records)
        for split, records in datasets.items()
    }

    document_ids = {
        passage["document_id"]
        for passage in passages
    }

    group_counts = Counter(
        question["group"]
        for question in questions
    )

    summary = {
        "total_questions": len(questions),
        "questions_by_split": split_counts,
        "unique_documents": len(document_ids),
        "unique_passages": len(passages),
        "groups": dict(group_counts),
        "total_passage_references": sum(
            len(question["passages"])
            for question in questions
        )
    }

    return summary


# ------------------------------------------------------------
# SAVE JSON
# ------------------------------------------------------------

def save_json(data, file_name):

    file_path = PROCESSED_DIR / file_name

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved: {file_path}")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    print("Loading ObliQA dataset...")

    datasets = {
        "train": load_json("ObliQA_train.json"),
        "dev": load_json("ObliQA_dev.json"),
        "test": load_json("ObliQA_test.json")
    }

    print("\nDataset records:")

    for split, records in datasets.items():
        print(f"{split}: {len(records)}")

    print("\nProcessing questions...")

    questions = process_questions(datasets)

    print("Extracting unique passages...")

    passages = extract_passages(questions)

    print("Creating dataset summary...")

    summary = create_summary(
        datasets,
        questions,
        passages
    )

    save_json(
        questions,
        "questions.json"
    )

    save_json(
        passages,
        "passages.json"
    )

    save_json(
        summary,
        "dataset_summary.json"
    )

    print("\n----------------------------------------")
    print("DATA PROCESSING COMPLETED")
    print("----------------------------------------")

    print(f"Total questions: {summary['total_questions']}")
    print(f"Unique documents: {summary['unique_documents']}")
    print(f"Unique passages: {summary['unique_passages']}")
    print(f"Total passage references: {summary['total_passage_references']}")


if __name__ == "__main__":
    main()