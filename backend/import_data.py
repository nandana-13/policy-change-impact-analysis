import json
from pathlib import Path
from datetime import date

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Policy,
    PolicyVersion,
    RegulatoryChange,
    PolicyRelationship,
    ImpactGroundTruth,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "synthetic_company_policies"
)


# ============================================================
# EXPECTED COUNTS
# ============================================================

EXPECTED_COUNTS = {
    "policies": 20,
    "policy_versions": 60,
    "regulatory_changes": 15,
    "policy_relationships": 12,
    "impact_ground_truth": 90,
}


# ============================================================
# JSON LOADER
# ============================================================

def load_json(filename):
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# DATE CONVERTER
# ============================================================

def parse_date(value):
    if not value:
        return None

    return date.fromisoformat(value)


# ============================================================
# IMPORT POLICIES
# ============================================================

def import_policies(db, records):

    inserted = 0
    skipped = 0

    for item in records:

        existing = (
            db.query(Policy)
            .filter(
                Policy.policy_id == item["policy_id"]
            )
            .first()
        )

        if existing:
            skipped += 1
            continue

        policy = Policy(
            policy_id=item["policy_id"],
            policy_name=item["policy_name"],
            category=item["category"],
            department=item["department"],
            description=item["description"],
            synthetic=item.get("synthetic", True),
        )

        db.add(policy)
        inserted += 1

    db.flush()

    print(
        f"Policies: {inserted} inserted, "
        f"{skipped} skipped"
    )


# ============================================================
# IMPORT POLICY VERSIONS
# ============================================================

def import_policy_versions(db, records):

    inserted = 0
    skipped = 0

    for item in records:

        existing = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_version_id
                == item["policy_version_id"]
            )
            .first()
        )

        if existing:
            skipped += 1
            continue

        policy_version = PolicyVersion(
            policy_version_id=item["policy_version_id"],
            policy_id=item["policy_id"],
            version_number=item["version_number"],
            effective_date=parse_date(
                item["effective_date"]
            ),
            change_description=item["change_description"],
            status=item["status"],
            synthetic=item.get("synthetic", True),
        )

        db.add(policy_version)
        inserted += 1

    db.flush()

    print(
        f"Policy versions: {inserted} inserted, "
        f"{skipped} skipped"
    )


# ============================================================
# IMPORT REGULATORY CHANGES
# ============================================================

def import_regulatory_changes(db, records):

    inserted = 0
    skipped = 0

    for item in records:

        existing = (
            db.query(RegulatoryChange)
            .filter(
                RegulatoryChange.regulatory_change_id
                == item["regulatory_change_id"]
            )
            .first()
        )

        if existing:
            skipped += 1
            continue

        change = RegulatoryChange(
            regulatory_change_id=item[
                "regulatory_change_id"
            ],
            regulatory_act=item[
                "regulatory_act"
            ],
            change_topic=item[
                "change_topic"
            ],
            change_description=item[
                "change_description"
            ],
            synthetic=item.get(
                "synthetic",
                True
            ),
        )

        db.add(change)
        inserted += 1

    db.flush()

    print(
        f"Regulatory changes: {inserted} inserted, "
        f"{skipped} skipped"
    )

# ============================================================
# IMPORT POLICY RELATIONSHIPS
# ============================================================

def import_policy_relationships(db, records):

    inserted = 0
    skipped = 0

    for item in records:

        existing = (
            db.query(PolicyRelationship)
            .filter(
                PolicyRelationship.relationship_id
                == item["relationship_id"]
            )
            .first()
        )

        if existing:
            skipped += 1
            continue

        relationship = PolicyRelationship(
            relationship_id=item[
                "relationship_id"
            ],
            source_policy_id=item[
                "source_policy_id"
            ],
            target_policy_id=item[
                "target_policy_id"
            ],
            relationship_type=item[
                "relationship_type"
            ],
            synthetic=item.get(
                "synthetic",
                True
            ),
        )

        db.add(relationship)
        inserted += 1

    db.flush()

    print(
        f"Policy relationships: {inserted} inserted, "
        f"{skipped} skipped"
    )
# ============================================================
# IMPORT IMPACT GROUND TRUTH
# ============================================================

def import_impact_ground_truth(db, records):

    inserted = 0
    skipped = 0

    for item in records:

        existing = (
            db.query(ImpactGroundTruth)
            .filter(
                ImpactGroundTruth.impact_id
                == item["impact_id"]
            )
            .first()
        )

        if existing:
            skipped += 1
            continue

        impact = ImpactGroundTruth(
            impact_id=item["impact_id"],
            regulatory_change_id=item[
                "regulatory_change_id"
            ],
            regulatory_act=item[
                "regulatory_act"
            ],
            change_topic=item[
                "change_topic"
            ],
            affected_policy_id=item[
                "affected_policy_id"
            ],
            relationship_type=item[
                "relationship_type"
            ],
            impact_type=item[
                "impact_type"
            ],
            expected_action=item[
                "expected_action"
            ],
            impact_status=item[
                "impact_status"
            ],
            evidence_policy_version=item[
                "evidence_policy_version"
            ],
            ground_truth_source=item[
                "ground_truth_source"
            ],
            synthetic=item.get(
                "synthetic",
                True
            ),
        )

        db.add(impact)
        inserted += 1

    db.flush()

    print(
        f"Impact ground truth: {inserted} inserted, "
        f"{skipped} skipped"
    )
# ============================================================
# VALIDATION
# ============================================================

def validate_counts(db):

    actual_counts = {
        "policies": db.query(Policy).count(),

        "policy_versions":
            db.query(PolicyVersion).count(),

        "regulatory_changes":
            db.query(RegulatoryChange).count(),

        "policy_relationships":
            db.query(PolicyRelationship).count(),

        "impact_ground_truth":
            db.query(ImpactGroundTruth).count(),
    }

    print()
    print("=" * 60)
    print("DATABASE VALIDATION")
    print("=" * 60)

    validation_passed = True

    for table_name, expected in EXPECTED_COUNTS.items():

        actual = actual_counts[table_name]

        status = "PASS" if actual == expected else "FAIL"

        print(
            f"{table_name:<25} "
            f"Expected: {expected:<5} "
            f"Actual: {actual:<5} "
            f"{status}"
        )

        if actual != expected:
            validation_passed = False

    print("=" * 60)

    if not validation_passed:
        raise RuntimeError(
            "Database validation failed."
        )

    print("DATABASE VALIDATION PASSED")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("POLICYLENS DATA IMPORT")
    print("=" * 60)

    print(f"Data directory:")
    print(DATA_DIR)
    print()

    # --------------------------------------------------------
    # Load JSON files
    # --------------------------------------------------------

    print("Loading JSON files...")

    policies = load_json("policies.json")
    policy_versions = load_json(
        "policy_versions.json"
    )
    regulatory_changes = load_json(
        "regulatory_changes.json"
    )
    policy_relationships = load_json(
        "policy_relationships.json"
    )
    impact_ground_truth = load_json(
        "impact_ground_truth.json"
    )

    print("JSON files loaded successfully.")
    print()

    # --------------------------------------------------------
    # Check source counts
    # --------------------------------------------------------

    print("Source data counts:")
    print(
        f"Policies              : {len(policies)}"
    )
    print(
        f"Policy versions       : {len(policy_versions)}"
    )
    print(
        f"Regulatory changes    : {len(regulatory_changes)}"
    )
    print(
        f"Policy relationships  : {len(policy_relationships)}"
    )
    print(
        f"Impact ground truth   : {len(impact_ground_truth)}"
    )
    print()

    # --------------------------------------------------------
    # Database session
    # --------------------------------------------------------

    db: Session = SessionLocal()

    try:

        print("Importing data...")
        print()

        import_policies(
            db,
            policies
        )

        import_policy_versions(
            db,
            policy_versions
        )

        import_regulatory_changes(
            db,
            regulatory_changes
        )

        import_policy_relationships(
            db,
            policy_relationships
        )

        import_impact_ground_truth(
            db,
            impact_ground_truth
        )

        # ----------------------------------------------------
        # Commit everything
        # ----------------------------------------------------

        db.commit()

        print()
        print("All data committed successfully.")

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        validate_counts(db)

    except Exception as e:

        db.rollback()

        print()
        print("IMPORT FAILED")
        print(f"Error: {e}")

        raise

    finally:

        db.close()

    print()
    print("=" * 60)
    print("POLICYLENS DATA IMPORT COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()