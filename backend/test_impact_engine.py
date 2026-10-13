from app.database import SessionLocal

from app.services.impact_engine_service import (
    get_impact_engine_service,
)


def print_separator():
    print("-" * 80)


def main():

    print("=" * 80)
    print("POLICYLENS")
    print("PHASE 2F.2 - DIRECT & INDIRECT IMPACT ANALYSIS")
    print("=" * 80)

    db = SessionLocal()

    try:

        service = get_impact_engine_service()

        regulatory_change_id = "CHG-001"

        print()
        print("REGULATORY CHANGE")
        print_separator()

        print(
            f"ID: {regulatory_change_id}"
        )

        result = (
            service.analyze_regulatory_change(
                db=db,
                regulatory_change_id=(
                    regulatory_change_id
                ),
                top_k=10,
                legal_top_k=8,
                policy_evidence_top_k=5,
            )
        )

        print()
        print("SUMMARY")
        print_separator()

        print(
            "Candidate count      : "
            f"{result['candidate_count']}"
        )

        print(
            "Direct impact count  : "
            f"{result['direct_impact_count']}"
        )

        print(
            "Indirect impact count: "
            f"{result['indirect_impact_count']}"
        )

        print(
            "No-impact count      : "
            f"{result['no_impact_count']}"
        )

        print()
        print("LEGAL EVIDENCE")
        print_separator()

        legal_evidence = result[
            "legal_evidence"
        ]

        print(
            f"Returned evidence: "
            f"{len(legal_evidence)}"
        )

        for index, evidence in enumerate(
            legal_evidence,
            start=1,
        ):

            print()
            print(
                f"Legal Evidence #{index}"
            )

            print(
                "Act       : "
                f"{evidence.get('act_title')}"
            )

            print(
                "Document  : "
                f"{evidence.get('document')}"
            )

            print(
                "Version   : "
                f"{evidence.get('version')}"
            )

            print(
                "Similarity: "
                f"{evidence.get('similarity'):.6f}"
            )

            print(
                "Evidence:"
            )

            print(
                evidence.get(
                    "evidence",
                    "",
                )
            )

        print()
        print("IMPACT ANALYSIS")
        print_separator()

        for index, item in enumerate(
            result["impacts"],
            start=1,
        ):

            print()
            print(
                f"Rank {index}"
            )

            print(
                "Policy ID       : "
                f"{item.get('policy_id')}"
            )

            print(
                "Policy name     : "
                f"{item.get('policy_name')}"
            )

            print(
                "Category        : "
                f"{item.get('category')}"
            )

            print(
                "Department      : "
                f"{item.get('department')}"
            )

            print(
                "Version         : "
                f"V{item.get('version_number')}"
            )

            print(
                "Policy version  : "
                f"{item.get('policy_version_id')}"
            )

            print(
                "Classification  : "
                f"{item.get('impact_classification')}"
            )

            print(
                "Impact type     : "
                f"{item.get('impact_type')}"
            )

            print(
                "Expected action : "
                f"{item.get('expected_action')}"
            )

            print(
                "Relevance       : "
                f"{item.get('relevance_score', 0.0):.6f}"
            )

            print(
                "Evidence align. : "
                f"{item.get('evidence_alignment', 0.0):.6f}"
            )

            print(
                "Direct score    : "
                f"{item.get('direct_score', 0.0):.6f}"
            )

            print(
                "Indirect score  : "
                f"{item.get('indirect_score', 0.0):.6f}"
            )

            print(
                "Reason:"
            )

            print(
                item.get(
                    "reason",
                    "",
                )
            )

            policy_evidence = item.get(
                "policy_evidence",
                [],
            )

            print()
            print(
                "Policy evidence count: "
                f"{len(policy_evidence)}"
            )

            for evidence_index, evidence in enumerate(
                policy_evidence[:2],
                start=1,
            ):

                print()
                print(
                    f"  Policy Evidence "
                    f"#{evidence_index}"
                )

                print(
                    "  Section: "
                    f"{evidence.get('section_title')}"
                )

                print(
                    "  Similarity: "
                    f"{evidence.get('similarity', 0.0):.6f}"
                )

                print(
                    "  Evidence:"
                )

                print(
                    "  "
                    + evidence.get(
                        "evidence",
                        "",
                    ).replace(
                        "\n",
                        "\n  ",
                    )
                )

            relationships = item.get(
                "indirect_relationships",
                [],
            )

            if relationships:

                print()
                print(
                    "Indirect relationships:"
                )

                for relationship in relationships:

                    print(
                        "  "
                        f"{relationship.get('source_policy_id')}"
                        " -> "
                        f"{relationship.get('target_policy_id')}"
                        " | "
                        f"{relationship.get('relationship_type')}"
                    )

        print()
        print("VALIDATION")
        print_separator()

        if result[
            "candidate_count"
        ] < 1:

            raise AssertionError(
                "No candidate policies "
                "were returned."
            )

        if len(
            result["legal_evidence"]
        ) < 1:

            raise AssertionError(
                "No legal evidence "
                "was returned."
            )

        for item in result["impacts"]:

            if not item.get(
                "policy_id"
            ):

                raise AssertionError(
                    "Impact item is missing "
                    "policy_id."
                )

            if item.get(
                "impact_classification"
            ) not in {
                "direct",
                "indirect",
                "no_impact",
            }:

                raise AssertionError(
                    "Invalid impact "
                    "classification."
                )

            if item.get(
                "expected_action"
            ) not in {
                "review_required",
                "monitor",
                "no_change_expected",
            }:

                raise AssertionError(
                    "Invalid expected "
                    "action."
                )

        print(
            "PASSED - Phase 2F.2 "
            "result structure is valid."
        )

        print()
        print("=" * 80)
        print(
            "PHASE 2F.2 TEST COMPLETED"
        )
        print("=" * 80)

    finally:

        db.close()


if __name__ == "__main__":
    main()