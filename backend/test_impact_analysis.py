import sys
from pathlib import Path

# ---------------------------------------------------------------
# Make backend importable when running from project root
# ---------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.database import SessionLocal
from app.services.impact_analysis_service import (
    get_impact_analysis_service,
)


def print_separator():
    print("=" * 80)


def main():

    print_separator()
    print("POLICYLENS")
    print("PHASE 2F.1 - REGULATORY CHANGE → CANDIDATE POLICIES")
    print_separator()

    db = SessionLocal()

    try:

        service = get_impact_analysis_service()

        # -------------------------------------------------------
        # Get first regulatory change
        # -------------------------------------------------------

        from app.models.regulatory_change import (
            RegulatoryChange,
        )

        regulatory_change = (
            db.query(RegulatoryChange)
            .order_by(RegulatoryChange.id)
            .first()
        )

        if regulatory_change is None:
            print(
                "ERROR: No regulatory changes found."
            )
            return

        print()
        print("REGULATORY CHANGE")
        print("-" * 80)

        print(
            f"ID          : "
            f"{regulatory_change.regulatory_change_id}"
        )

        print(
            f"Act         : "
            f"{regulatory_change.regulatory_act}"
        )

        print(
            f"Topic       : "
            f"{regulatory_change.change_topic}"
        )

        print(
            f"Description : "
            f"{regulatory_change.change_description}"
        )

        # -------------------------------------------------------
        # Build query
        # -------------------------------------------------------

        query = service.build_policy_query(
            regulatory_change
        )

        print()
        print("RETRIEVAL QUERY")
        print("-" * 80)
        print(query)

        # -------------------------------------------------------
        # Candidate retrieval
        # -------------------------------------------------------

        result = service.analyze_regulatory_change(
            db=db,
            regulatory_change_id=(
                regulatory_change.regulatory_change_id
            ),
            top_k=10,
        )

        print()
        print("CANDIDATE POLICIES")
        print("-" * 80)

        print(
            f"Candidate count: "
            f"{result['candidate_count']}"
        )

        print()

        for index, candidate in enumerate(
            result["candidates"],
            start=1,
        ):

            print(f"Rank {index}")
            print(
                f"Policy ID       : "
                f"{candidate['policy_id']}"
            )

            print(
                f"Policy name     : "
                f"{candidate['policy_name']}"
            )

            print(
                f"Category        : "
                f"{candidate['category']}"
            )

            print(
                f"Department      : "
                f"{candidate['department']}"
            )

            print(
                f"Version         : "
                f"V{candidate['version_number']}"
                if candidate["version_number"] is not None
                else "Version         : N/A"
            )

            print(
                f"Policy version  : "
                f"{candidate['policy_version_id']}"
            )

            print(
                f"Effective date  : "
                f"{candidate['effective_date']}"
            )

            print(
                f"Status          : "
                f"{candidate['status']}"
            )

            print(
                f"Relevance       : "
                f"{candidate['relevance_score']:.6f}"
            )

            print(
                f"Semantic        : "
                f"{candidate['semantic_score']:.6f}"
            )

            print(
                f"Lexical         : "
                f"{candidate['lexical_score']:.6f}"
            )

            print(
                f"Term overlap    : "
                f"{candidate['term_overlap_score']:.6f}"
            )

            print(
                f"Section         : "
                f"{candidate['section_score']:.6f}"
            )

            print(
                f"Subject         : "
                f"{candidate['subject_score']:.6f}"
            )

            print(
                f"Matched section : "
                f"{candidate['matched_section']}"
            )

            print("Evidence:")

            evidence = candidate["evidence"]

            if evidence:
                print(evidence[:1200])
            else:
                print("No evidence returned.")

            print()
            print("-" * 80)

        # -------------------------------------------------------
        # Validation
        # -------------------------------------------------------

        print()
        print("VALIDATION")
        print("-" * 80)

        candidates = result["candidates"]

        if not candidates:
            print(
                "FAILED - No candidate policies returned."
            )
            return

        required_fields = [
            "policy_id",
            "policy_name",
            "category",
            "department",
            "relevance_score",
            "evidence",
        ]

        validation_passed = True

        for candidate in candidates:

            for field in required_fields:

                if field not in candidate:
                    print(
                        f"FAILED - Missing field: {field}"
                    )

                    validation_passed = False

        if validation_passed:
            print(
                "PASSED - Candidate policy structure "
                "is valid."
            )

        # -------------------------------------------------------
        # Final
        # -------------------------------------------------------

        print()
        print_separator()
        print(
            "PHASE 2F.1 TEST COMPLETED"
        )
        print_separator()

    finally:
        db.close()


if __name__ == "__main__":
    main()