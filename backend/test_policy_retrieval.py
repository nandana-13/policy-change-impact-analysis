from app.services.policy_retrieval_service import (
    get_policy_retrieval_service
)


def print_results(
    title,
    query,
    results
):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    print("Query:")
    print(query)

    if not results:

        print()
        print("NO RESULTS")

        return

    for index, result in enumerate(
        results,
        start=1
    ):

        print()
        print(f"Rank {index}")

        print(
            f"Rerank score : "
            f"{result['rerank_score']:.6f}"
        )

        print(
            f"Semantic     : "
            f"{result['semantic_score']:.6f}"
        )

        print(
            f"Lexical      : "
            f"{result['lexical_score']:.6f}"
        )

        print(
            f"Term overlap : "
            f"{result['term_overlap_score']:.6f}"
        )

        print(
            f"Section      : "
            f"{result['section_score']:.6f}"
        )

        print(
            f"Subject      : "
            f"{result['subject_score']:.6f}"
        )

        print(
            f"Policy       : "
            f"{result['policy_id']}"
        )

        print(
            f"Policy name  : "
            f"{result['policy_name']}"
        )

        print(
            f"Version      : "
            f"V{result['version_number']}"
        )

        print(
            f"Effective    : "
            f"{result['effective_date']}"
        )

        print(
            f"Section      : "
            f"{result['section_title']}"
        )

        print(
            f"Status       : "
            f"{result['status']}"
        )

        print("Evidence:")

        evidence = result[
            "evidence"
        ]

        print(
            evidence[:900]
        )


def main():

    print()
    print("=" * 70)
    print("POLICYLENS")
    print("PHASE 2E.3 - INTENT-AWARE RETRIEVAL TEST")
    print("=" * 70)

    service = (
        get_policy_retrieval_service()
    )

    # =========================================================
    # TEST 1
    # EMPLOYEE VS CUSTOMER
    # =========================================================

    query_1 = (
        "What requirements apply to "
        "protecting employee personal data?"
    )

    results_1 = service.retrieve(
        query=query_1,
        top_k=5,
    )

    print_results(
        "TEST 1 - EMPLOYEE DATA PROTECTION",
        query_1,
        results_1,
    )

    # =========================================================
    # TEST 2
    # RETENTION AND DISPOSAL
    # =========================================================

    query_2 = (
        "What requirements apply to employee "
        "data retention and disposal?"
    )

    results_2 = service.retrieve(
        query=query_2,
        top_k=5,
    )

    print_results(
        "TEST 2 - RETENTION AND DISPOSAL",
        query_2,
        results_2,
    )

    # =========================================================
    # TEST 3
    # MONITORING AND REVIEW
    # =========================================================

    query_3 = (
        "How is compliance with the policy "
        "monitored and reviewed?"
    )

    results_3 = service.retrieve(
        query=query_3,
        top_k=5,
    )

    print_results(
        "TEST 3 - MONITORING AND REVIEW",
        query_3,
        results_3,
    )

    # =========================================================
    # TEST 4
    # RECORDS AND EVIDENCE
    # =========================================================

    query_4 = (
        "What records and evidence "
        "must be maintained?"
    )

    results_4 = service.retrieve(
        query=query_4,
        top_k=5,
    )

    print_results(
        "TEST 4 - RECORDS AND EVIDENCE",
        query_4,
        results_4,
    )

    # =========================================================
    # TEST 5
    # VERSION-AWARE RETRIEVAL
    # =========================================================

    query_5 = (
        "What requirements apply to "
        "employee data protection?"
    )

    as_of_date = "2026-01-01"

    results_5 = service.retrieve(
        query=query_5,
        top_k=10,
        policy_id="POL-001",
        as_of_date=as_of_date,
    )

    print_results(
        "TEST 5 - VERSION-AWARE RETRIEVAL",
        query_5,
        results_5,
    )

    # =========================================================
    # VERSION VALIDATION
    # =========================================================

    print()
    print("=" * 70)
    print("VERSION VALIDATION")
    print("=" * 70)

    invalid_dates = []

    for result in results_5:

        effective_date = str(
            result["effective_date"]
        )

        if effective_date > as_of_date:

            invalid_dates.append(
                effective_date
            )

    if invalid_dates:

        print(
            "FAILED - Found versions after "
            "the requested as-of date:"
        )

        for date in invalid_dates:

            print(
                f"  {date}"
            )

    else:

        print(
            "PASSED - All retrieved versions "
            "are valid for the requested date."
        )

    # =========================================================
    # TEST 6
    # POLICY-SPECIFIC RETRIEVAL
    # =========================================================

    query_6 = (
        "What controls and requirements "
        "apply to financial reporting?"
    )

    results_6 = service.retrieve(
        query=query_6,
        top_k=5,
        policy_id="POL-009",
    )

    print_results(
        "TEST 6 - FINANCIAL REPORTING POLICY",
        query_6,
        results_6,
    )

    # =========================================================
    # TEST 7
    # ROLES AND RESPONSIBILITIES
    # =========================================================

    query_7 = (
        "Who is responsible for implementing "
        "and maintaining this policy?"
    )

    results_7 = service.retrieve(
        query=query_7,
        top_k=5,
    )

    print_results(
        "TEST 7 - ROLES AND RESPONSIBILITIES",
        query_7,
        results_7,
    )

    # =========================================================
    # TEST 8
    # EXCEPTIONS AND ESCALATION
    # =========================================================

    query_8 = (
        "What exceptions are permitted and "
        "when should issues be escalated?"
    )

    results_8 = service.retrieve(
        query=query_8,
        top_k=5,
    )

    print_results(
        "TEST 8 - EXCEPTIONS AND ESCALATION",
        query_8,
        results_8,
    )

    # =========================================================
    # TEST 9
    # RELATED POLICIES
    # =========================================================

    query_9 = (
        "Which policies and controls are "
        "related to this policy?"
    )

    results_9 = service.retrieve(
        query=query_9,
        top_k=5,
    )

    print_results(
        "TEST 9 - RELATED POLICIES AND CONTROLS",
        query_9,
        results_9,
    )

    # =========================================================
    # FINAL STATUS
    # =========================================================

    print()
    print("=" * 70)
    print("PHASE 2E.3 RETRIEVAL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":

    main()