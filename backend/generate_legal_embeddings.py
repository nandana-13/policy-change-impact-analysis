from pathlib import Path
import sys


# ------------------------------------------------------------------
# PolicyLens project root
# ------------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


# ------------------------------------------------------------------
# Make backend importable
# ------------------------------------------------------------------

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)


# ------------------------------------------------------------------
# Import PolicyLens embedding service
# ------------------------------------------------------------------

from backend.app.services.legal_embedding_service import (
    LegalEmbeddingService
)


# ------------------------------------------------------------------
# Phase 2A input
# ------------------------------------------------------------------

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "legal_rag"
    / "legal_chunks.parquet"
)


# ------------------------------------------------------------------
# Phase 2B output
# ------------------------------------------------------------------

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "legal_rag"
    / "embeddings"
)


def main():

    print("=" * 70)
    print("POLICYLENS")
    print("PHASE 2B - LOCAL LEGAL EMBEDDINGS")
    print("=" * 70)

    print(
        f"\nInput file:"
        f"\n{INPUT_FILE}"
    )

    print(
        f"\nOutput directory:"
        f"\n{OUTPUT_DIRECTORY}"
    )

    # --------------------------------------------------------------
    # Verify Phase 2A output
    # --------------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(

            "\nPhase 2A output was not found.\n\n"

            f"Expected:\n{INPUT_FILE}\n\n"

            "Please complete Phase 2A first."
        )

    # --------------------------------------------------------------
    # Create service
    # --------------------------------------------------------------

    service = LegalEmbeddingService()

    # --------------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------------

    result = service.generate_embeddings(

        input_file=INPUT_FILE,

        output_directory=OUTPUT_DIRECTORY
    )

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    print("\n" + "=" * 70)
    print("POLICYLENS PHASE 2B COMPLETE")
    print("=" * 70)

    print(
        f"\nLegal chunks:"
        f" {result['total_chunks']:,}"
    )

    print(
        f"Embeddings:"
        f" {result['total_embeddings']:,}"
    )

    print(
        f"Dimensions:"
        f" {result['dimension']}"
    )

    print(
        f"Vocabulary:"
        f" {result['vocabulary_size']:,}"
    )

    print(
        f"Explained variance:"
        f" {result['explained_variance'] * 100:.2f}%"
    )

    print(
        f"\nMethod:"
        f" {result['method']}"
    )

    print(
        "\nNext phase:"
        " Phase 2C - ChromaDB"
    )


if __name__ == "__main__":
    main()