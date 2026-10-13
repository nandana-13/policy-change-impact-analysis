from app.services.legal_retrieval_service import (
    LegalRetrievalService
)


# ============================================================
# POLICYLENS
# PHASE 2D - RETRIEVAL TEST
# ============================================================


def print_separator():
    print()
    print("=" * 70)


def main():

    print_separator()

    print(
        "POLICYLENS"
    )

    print(
        "PHASE 2D - VERSION-AWARE LEGAL RETRIEVAL"
    )

    print_separator()

    # --------------------------------------------------------
    # LOAD SERVICE
    # --------------------------------------------------------

    service = LegalRetrievalService()

    print_separator()

    # --------------------------------------------------------
    # TEST 1
    # General semantic retrieval
    # --------------------------------------------------------

    query_1 = (
        "What requirements apply to "
        "personal data protection and "
        "accountability?"
    )

    print(
        "TEST 1 - GENERAL LEGAL RETRIEVAL"
    )

    print(
        f"\nQuery:\n{query_1}"
    )

    result_1 = service.retrieve(
        query=query_1,
        top_k=5,
    )

    print(
        f"\nReturned evidence: "
        f"{result_1['retrieval']['returned_count']}"
    )

    for item in result_1["evidence"]:

        source = item["source"]

        print()
        print(
            f"Rank: "
            f"{item['rank']}"
        )

        print(
            f"Similarity: "
            f"{item['similarity_score']}"
        )

        print(
            f"Act: "
            f"{source['act_title']}"
        )

        print(
            f"Version: "
            f"{source['version']}"
        )

        print(
            f"Effective date: "
            f"{source['effective_date']}"
        )

        print(
            f"Chunk ID: "
            f"{source['chunk_id']}"
        )

        print(
            "Evidence:"
        )

        print(
            item["evidence_text"][:500]
        )

    # --------------------------------------------------------
    # TEST 2
    # Act-specific retrieval
    # --------------------------------------------------------

    query_2 = (
        "What obligations apply to "
        "personal data processing?"
    )

    print_separator()

    print(
        "TEST 2 - ACT-SPECIFIC RETRIEVAL"
    )

    print(
        f"\nQuery:\n{query_2}"
    )

    result_2 = service.retrieve(

        query=query_2,

        top_k=5,

        act_title=(
            "Data Protection Act 2018"
        ),

    )

    print(
        f"\nReturned evidence: "
        f"{result_2['retrieval']['returned_count']}"
    )

    for item in result_2["evidence"]:

        source = item["source"]

        print(
            f"\n{item['rank']}. "
            f"{source['act_title']} | "
            f"version={source['version']} | "
            f"effective={source['effective_date']} | "
            f"similarity={item['similarity_score']}"
        )

        print(
            item["evidence_text"][:400]
        )

    # --------------------------------------------------------
    # TEST 3
    # Version-aware / as-of-date retrieval
    # --------------------------------------------------------

    query_3 = (
        "What requirements apply to "
        "retaining personal data?"
    )

    print_separator()

    print(
        "TEST 3 - VERSION-AWARE RETRIEVAL"
    )

    print(
        f"\nQuery:\n{query_3}"
    )

    print(
        "\nAs-of date: 2020-01-01"
    )

    result_3 = service.retrieve(

        query=query_3,

        top_k=5,

        as_of_date="2020-01-01",

        act_title=(
            "Data Protection Act 2018"
        ),

    )

    print(
        f"\nReturned evidence: "
        f"{result_3['retrieval']['returned_count']}"
    )

    for item in result_3["evidence"]:

        source = item["source"]

        print(
            f"\n{item['rank']}. "
            f"{source['act_title']} | "
            f"version={source['version']} | "
            f"effective={source['effective_date']} | "
            f"similarity={item['similarity_score']}"
        )

        print(
            "Evidence:"
        )

        print(
            item["evidence_text"][:500]
        )

    # --------------------------------------------------------
    # TEST 4
    # Metadata verification
    # --------------------------------------------------------

    print_separator()

    print(
        "TEST 4 - SOURCE METADATA VALIDATION"
    )

    if not result_1["evidence"]:

        raise RuntimeError(
            "No evidence returned from Test 1."
        )

    required_fields = [

        "chunk_id",
        "act_title",
        "document",
        "version",
        "effective_date",
        "source",
        "jurisdiction",
        "file_path",

    ]

    source = result_1[
        "evidence"
    ][0]["source"]

    for field in required_fields:

        if field not in source:

            raise RuntimeError(
                f"Missing source metadata: "
                f"{field}"
            )

        print(
            f"{field}: "
            f"{source[field]}"
        )

    print_separator()

    print(
        "PHASE 2D RETRIEVAL TESTS COMPLETED"
    )

    print_separator()


if __name__ == "__main__":
    main()