import json
import random
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

BASE_DIR = Path(__file__).resolve().parents[3]

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "synthetic_company_policies"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

random.seed(SEED)


# ============================================================
# 1. COMPANY POLICIES
# ============================================================

POLICIES = [
    # DATA PRIVACY
    {
        "policy_id": "POL-001",
        "policy_name": "Employee Data Protection Policy",
        "category": "Data Privacy",
        "department": "Human Resources",
        "description": "Defines organizational requirements for collecting, processing, storing and protecting employee information.",
    },
    {
        "policy_id": "POL-002",
        "policy_name": "Customer Data Protection Policy",
        "category": "Data Privacy",
        "department": "Information Technology",
        "description": "Defines controls for handling customer personal information across organizational systems.",
    },
    {
        "policy_id": "POL-003",
        "policy_name": "Data Retention Policy",
        "category": "Data Privacy",
        "department": "Information Technology",
        "description": "Defines retention periods, review procedures and disposal requirements for organizational records.",
    },
    {
        "policy_id": "POL-004",
        "policy_name": "Data Incident Response Policy",
        "category": "Data Privacy",
        "department": "Information Security",
        "description": "Defines organizational procedures for identifying, recording and responding to data-related incidents.",
    },

    # HUMAN RESOURCES
    {
        "policy_id": "POL-005",
        "policy_name": "Equal Opportunity Policy",
        "category": "Human Resources",
        "department": "Human Resources",
        "description": "Defines fair and consistent principles for employment and workplace decision-making.",
    },
    {
        "policy_id": "POL-006",
        "policy_name": "Recruitment and Selection Policy",
        "category": "Human Resources",
        "department": "Human Resources",
        "description": "Defines standardized recruitment, selection and candidate assessment procedures.",
    },
    {
        "policy_id": "POL-007",
        "policy_name": "Workplace Accommodation Policy",
        "category": "Human Resources",
        "department": "Human Resources",
        "description": "Defines procedures for requesting, reviewing and documenting workplace accommodations.",
    },
    {
        "policy_id": "POL-008",
        "policy_name": "Employee Grievance Policy",
        "category": "Human Resources",
        "department": "Human Resources",
        "description": "Defines procedures for submitting, reviewing and resolving employee grievances.",
    },

    # FINANCE
    {
        "policy_id": "POL-009",
        "policy_name": "Financial Reporting Policy",
        "category": "Finance",
        "department": "Finance",
        "description": "Defines procedures for preparing, reviewing and maintaining financial reports.",
    },
    {
        "policy_id": "POL-010",
        "policy_name": "Tax Compliance Policy",
        "category": "Finance",
        "department": "Finance",
        "description": "Defines internal procedures for identifying, reviewing and documenting tax-related obligations.",
    },
    {
        "policy_id": "POL-011",
        "policy_name": "Expense Management Policy",
        "category": "Finance",
        "department": "Finance",
        "description": "Defines approval, documentation and reimbursement procedures for business expenses.",
    },
    {
        "policy_id": "POL-012",
        "policy_name": "Financial Audit Policy",
        "category": "Finance",
        "department": "Internal Audit",
        "description": "Defines procedures for financial audit planning, evidence collection and review.",
    },

    # PAYROLL AND TAX
    {
        "policy_id": "POL-013",
        "policy_name": "Payroll Processing Policy",
        "category": "Payroll and Tax",
        "department": "Payroll",
        "description": "Defines procedures for calculating, reviewing and processing employee payroll.",
    },
    {
        "policy_id": "POL-014",
        "policy_name": "Employee Benefits Policy",
        "category": "Payroll and Tax",
        "department": "Human Resources",
        "description": "Defines procedures for administering employee benefits and maintaining supporting records.",
    },
    {
        "policy_id": "POL-015",
        "policy_name": "Compensation Records Policy",
        "category": "Payroll and Tax",
        "department": "Payroll",
        "description": "Defines procedures for maintaining employee compensation and payroll-related records.",
    },
    {
        "policy_id": "POL-016",
        "policy_name": "Payroll Audit Policy",
        "category": "Payroll and Tax",
        "department": "Internal Audit",
        "description": "Defines procedures for reviewing payroll records, controls and audit evidence.",
    },

    # LOCAL GOVERNANCE
    {
        "policy_id": "POL-017",
        "policy_name": "Local Procurement Policy",
        "category": "Local Governance",
        "department": "Procurement",
        "description": "Defines procedures for local procurement, supplier selection and procurement documentation.",
    },
    {
        "policy_id": "POL-018",
        "policy_name": "Property and Planning Policy",
        "category": "Local Governance",
        "department": "Facilities",
        "description": "Defines internal procedures for property-related planning and project documentation.",
    },
    {
        "policy_id": "POL-019",
        "policy_name": "Community Engagement Policy",
        "category": "Local Governance",
        "department": "Corporate Affairs",
        "description": "Defines procedures for documenting and managing community engagement activities.",
    },
    {
        "policy_id": "POL-020",
        "policy_name": "Local Regulatory Compliance Policy",
        "category": "Local Governance",
        "department": "Compliance",
        "description": "Defines procedures for monitoring and documenting local regulatory requirements.",
    },
]


# ============================================================
# 2. POLICY VERSION CHANGES
# ============================================================

VERSION_CHANGES = {
    "POL-001": [
        "Added employee-data access review procedures.",
        "Updated internal record-retention review procedures.",
    ],
    "POL-002": [
        "Added customer-data access monitoring.",
        "Updated data handling documentation requirements.",
    ],
    "POL-003": [
        "Reduced internal retention review interval.",
        "Added documented disposal verification.",
    ],
    "POL-004": [
        "Added incident documentation review.",
        "Updated escalation and evidence-recording procedures.",
    ],

    "POL-005": [
        "Added standardized employment decision documentation.",
        "Updated review procedures for workplace decisions.",
    ],
    "POL-006": [
        "Added structured candidate assessment documentation.",
        "Updated recruitment review procedures.",
    ],
    "POL-007": [
        "Added accommodation request documentation.",
        "Updated accommodation review procedures.",
    ],
    "POL-008": [
        "Added grievance case-record review.",
        "Updated grievance escalation documentation.",
    ],

    "POL-009": [
        "Added financial reporting review checkpoints.",
        "Updated supporting-record documentation.",
    ],
    "POL-010": [
        "Added tax review documentation.",
        "Updated internal tax record checks.",
    ],
    "POL-011": [
        "Added expense evidence requirements.",
        "Updated expense approval documentation.",
    ],
    "POL-012": [
        "Added audit evidence review procedures.",
        "Updated financial audit documentation.",
    ],

    "POL-013": [
        "Added payroll calculation review.",
        "Updated payroll record verification procedures.",
    ],
    "POL-014": [
        "Added benefits-record review procedures.",
        "Updated benefits administration documentation.",
    ],
    "POL-015": [
        "Added compensation record verification.",
        "Updated payroll record retention procedures.",
    ],
    "POL-016": [
        "Added payroll audit evidence checks.",
        "Updated audit sampling documentation.",
    ],

    "POL-017": [
        "Added supplier-selection documentation.",
        "Updated procurement review procedures.",
    ],
    "POL-018": [
        "Added planning documentation checkpoints.",
        "Updated property project review procedures.",
    ],
    "POL-019": [
        "Added community engagement records.",
        "Updated stakeholder documentation procedures.",
    ],
    "POL-020": [
        "Added local compliance monitoring.",
        "Updated regulatory review documentation.",
    ],
}


def generate_policy_versions():

    versions = []

    for policy in POLICIES:

        policy_id = policy["policy_id"]

        for version_number in range(1, 4):

            if version_number == 1:

                change_description = (
                    "Initial policy version."
                )

            else:

                change_description = VERSION_CHANGES[
                    policy_id
                ][version_number - 2]

            versions.append(
                {
                    "policy_version_id": (
                        f"{policy_id}-V{version_number}"
                    ),
                    "policy_id": policy_id,
                    "version_number": version_number,
                    "effective_date": (
                        f"202{version_number + 1}-"
                        f"0{version_number}-01"
                    ),
                    "change_description": change_description,
                    "status": (
                        "baseline"
                        if version_number == 1
                        else "revised"
                    ),
                    "synthetic": True,
                }
            )

    return versions


# ============================================================
# 3. REGULATORY CHANGE SCENARIOS
# ============================================================

REGULATORY_CHANGES = [
    {
        "regulatory_change_id": "CHG-001",
        "regulatory_act": "data_protection_act_2018",
        "change_topic": "data_retention",
        "change_description": "Synthetic scenario involving a change to organizational handling and review of retained personal-data records.",
    },
    {
        "regulatory_change_id": "CHG-002",
        "regulatory_act": "data_protection_act_2018",
        "change_topic": "data_access_control",
        "change_description": "Synthetic scenario involving updated expectations for reviewing access to personal-data systems.",
    },
    {
        "regulatory_change_id": "CHG-003",
        "regulatory_act": "data_protection_act_2018",
        "change_topic": "incident_documentation",
        "change_description": "Synthetic scenario involving changes to internal documentation of data-related incidents.",
    },

    {
        "regulatory_change_id": "CHG-004",
        "regulatory_act": "equality_act_2010",
        "change_topic": "employment_decision_process",
        "change_description": "Synthetic scenario involving standardized documentation of employment-related decisions.",
    },
    {
        "regulatory_change_id": "CHG-005",
        "regulatory_act": "equality_act_2010",
        "change_topic": "workplace_accommodation",
        "change_description": "Synthetic scenario involving updates to internal review and documentation of workplace accommodations.",
    },
    {
        "regulatory_change_id": "CHG-006",
        "regulatory_act": "equality_act_2010",
        "change_topic": "grievance_documentation",
        "change_description": "Synthetic scenario involving changes to documentation and review of workplace grievances.",
    },

    {
        "regulatory_change_id": "CHG-007",
        "regulatory_act": "finance_act_2003",
        "change_topic": "financial_reporting",
        "change_description": "Synthetic scenario involving additional internal review of financial reporting records.",
    },
    {
        "regulatory_change_id": "CHG-008",
        "regulatory_act": "finance_act_2003",
        "change_topic": "expense_documentation",
        "change_description": "Synthetic scenario involving updated documentation for business expense processing.",
    },
    {
        "regulatory_change_id": "CHG-009",
        "regulatory_act": "finance_act_2003",
        "change_topic": "financial_audit",
        "change_description": "Synthetic scenario involving changes to financial audit evidence and review procedures.",
    },

    {
        "regulatory_change_id": "CHG-010",
        "regulatory_act": "income_tax_earnings_pensions_act_2003",
        "change_topic": "payroll_processing",
        "change_description": "Synthetic scenario involving changes to payroll processing review procedures.",
    },
    {
        "regulatory_change_id": "CHG-011",
        "regulatory_act": "income_tax_earnings_pensions_act_2003",
        "change_topic": "compensation_records",
        "change_description": "Synthetic scenario involving updated review of employee compensation records.",
    },
    {
        "regulatory_change_id": "CHG-012",
        "regulatory_act": "income_tax_earnings_pensions_act_2003",
        "change_topic": "payroll_audit",
        "change_description": "Synthetic scenario involving changes to payroll audit evidence and review.",
    },

    {
        "regulatory_change_id": "CHG-013",
        "regulatory_act": "localism_act_2011",
        "change_topic": "local_procurement",
        "change_description": "Synthetic scenario involving updated documentation for local procurement activities.",
    },
    {
        "regulatory_change_id": "CHG-014",
        "regulatory_act": "localism_act_2011",
        "change_topic": "planning_documentation",
        "change_description": "Synthetic scenario involving changes to property and planning documentation.",
    },
    {
        "regulatory_change_id": "CHG-015",
        "regulatory_act": "localism_act_2011",
        "change_topic": "community_engagement",
        "change_description": "Synthetic scenario involving updated internal documentation for community engagement.",
    },
]


# ============================================================
# 4. POLICY DEPENDENCIES
# ============================================================

POLICY_DEPENDENCIES = [
    ("POL-001", "POL-003", "depends_on"),
    ("POL-002", "POL-003", "depends_on"),
    ("POL-004", "POL-003", "depends_on"),
    ("POL-006", "POL-005", "supports"),
    ("POL-007", "POL-008", "supports"),
    ("POL-009", "POL-012", "supports"),
    ("POL-010", "POL-009", "supports"),
    ("POL-013", "POL-015", "supports"),
    ("POL-015", "POL-016", "supports"),
    ("POL-017", "POL-020", "supports"),
    ("POL-018", "POL-020", "supports"),
    ("POL-019", "POL-020", "supports"),
]


def generate_policy_relationships():

    relationships = []

    for index, (
        source,
        target,
        relationship_type
    ) in enumerate(
        POLICY_DEPENDENCIES,
        start=1
    ):

        relationships.append(
            {
                "relationship_id": f"REL-{index:03d}",
                "source_policy_id": source,
                "target_policy_id": target,
                "relationship_type": relationship_type,
                "synthetic": True,
            }
        )

    return relationships


# ============================================================
# 5. CONTROLLED IMPACT DESIGN
# ============================================================
#
# IMPORTANT:
#
# We explicitly create:
#
# 30 DIRECT
# 30 INDIRECT
# 30 NO-IMPACT
#
# = 90 total
#
# Every regulatory scenario gets exactly:
#
# 2 direct
# 2 indirect
# 2 no-impact
#
# ============================================================

IMPACT_RULES = {

    "CHG-001": [
        ("POL-003", "direct", "recordkeeping"),
        ("POL-001", "direct", "process"),
        ("POL-002", "indirect", "process"),
        ("POL-004", "indirect", "documentation"),
        ("POL-005", "no_impact", "none"),
        ("POL-006", "no_impact", "none"),
    ],

    "CHG-002": [
        ("POL-001", "direct", "process"),
        ("POL-002", "direct", "process"),
        ("POL-003", "indirect", "recordkeeping"),
        ("POL-004", "indirect", "process"),
        ("POL-007", "no_impact", "none"),
        ("POL-009", "no_impact", "none"),
    ],

    "CHG-003": [
        ("POL-004", "direct", "documentation"),
        ("POL-003", "direct", "recordkeeping"),
        ("POL-001", "indirect", "documentation"),
        ("POL-002", "indirect", "documentation"),
        ("POL-005", "no_impact", "none"),
        ("POL-010", "no_impact", "none"),
    ],

    "CHG-004": [
        ("POL-005", "direct", "process"),
        ("POL-006", "direct", "process"),
        ("POL-007", "indirect", "documentation"),
        ("POL-008", "indirect", "process"),
        ("POL-013", "no_impact", "none"),
        ("POL-017", "no_impact", "none"),
    ],

    "CHG-005": [
        ("POL-007", "direct", "process"),
        ("POL-005", "direct", "process"),
        ("POL-008", "indirect", "documentation"),
        ("POL-006", "indirect", "documentation"),
        ("POL-009", "no_impact", "none"),
        ("POL-013", "no_impact", "none"),
    ],

    "CHG-006": [
        ("POL-008", "direct", "documentation"),
        ("POL-005", "direct", "process"),
        ("POL-007", "indirect", "documentation"),
        ("POL-006", "indirect", "process"),
        ("POL-011", "no_impact", "none"),
        ("POL-018", "no_impact", "none"),
    ],

    "CHG-007": [
        ("POL-009", "direct", "recordkeeping"),
        ("POL-012", "direct", "documentation"),
        ("POL-010", "indirect", "recordkeeping"),
        ("POL-011", "indirect", "process"),
        ("POL-013", "no_impact", "none"),
        ("POL-019", "no_impact", "none"),
    ],

    "CHG-008": [
        ("POL-011", "direct", "documentation"),
        ("POL-009", "direct", "process"),
        ("POL-012", "indirect", "documentation"),
        ("POL-010", "indirect", "process"),
        ("POL-006", "no_impact", "none"),
        ("POL-018", "no_impact", "none"),
    ],

    "CHG-009": [
        ("POL-012", "direct", "documentation"),
        ("POL-009", "direct", "recordkeeping"),
        ("POL-011", "indirect", "documentation"),
        ("POL-010", "indirect", "recordkeeping"),
        ("POL-001", "no_impact", "none"),
        ("POL-017", "no_impact", "none"),
    ],

    "CHG-010": [
        ("POL-013", "direct", "process"),
        ("POL-014", "direct", "process"),
        ("POL-015", "indirect", "recordkeeping"),
        ("POL-016", "indirect", "documentation"),
        ("POL-005", "no_impact", "none"),
        ("POL-017", "no_impact", "none"),
    ],

    "CHG-011": [
        ("POL-015", "direct", "recordkeeping"),
        ("POL-014", "direct", "recordkeeping"),
        ("POL-013", "indirect", "process"),
        ("POL-016", "indirect", "documentation"),
        ("POL-002", "no_impact", "none"),
        ("POL-018", "no_impact", "none"),
    ],

    "CHG-012": [
        ("POL-016", "direct", "documentation"),
        ("POL-013", "direct", "process"),
        ("POL-015", "indirect", "recordkeeping"),
        ("POL-014", "indirect", "documentation"),
        ("POL-005", "no_impact", "none"),
        ("POL-019", "no_impact", "none"),
    ],

    "CHG-013": [
        ("POL-017", "direct", "process"),
        ("POL-020", "direct", "documentation"),
        ("POL-018", "indirect", "process"),
        ("POL-019", "indirect", "documentation"),
        ("POL-009", "no_impact", "none"),
        ("POL-013", "no_impact", "none"),
    ],

    "CHG-014": [
        ("POL-018", "direct", "documentation"),
        ("POL-020", "direct", "process"),
        ("POL-017", "indirect", "documentation"),
        ("POL-019", "indirect", "process"),
        ("POL-005", "no_impact", "none"),
        ("POL-013", "no_impact", "none"),
    ],

    "CHG-015": [
        ("POL-019", "direct", "documentation"),
        ("POL-020", "direct", "process"),
        ("POL-018", "indirect", "documentation"),
        ("POL-017", "indirect", "process"),
        ("POL-005", "no_impact", "none"),
        ("POL-009", "no_impact", "none"),
    ],
}


# ============================================================
# 6. EXPECTED ACTION
# ============================================================

def get_expected_action(relationship_type):

    if relationship_type == "direct":
        return "review_required"

    if relationship_type == "indirect":
        return "monitor"

    return "no_change_expected"


def get_impact_status(relationship_type):

    if relationship_type in ["direct", "indirect"]:
        return "potentially_affected"

    return "not_affected"


# ============================================================
# 7. EVIDENCE VERSION
# ============================================================

def get_evidence_version(
    policy_id,
    relationship_type
):

    if relationship_type == "direct":
        return f"{policy_id}-V3"

    if relationship_type == "indirect":
        return f"{policy_id}-V2"

    return f"{policy_id}-V1"


# ============================================================
# 8. GENERATE GROUND TRUTH
# ============================================================

def generate_ground_truth():

    ground_truth = []

    counter = 1

    for change in REGULATORY_CHANGES:

        change_id = change[
            "regulatory_change_id"
        ]

        rules = IMPACT_RULES[change_id]

        for (
            policy_id,
            relationship_type,
            impact_type
        ) in rules:

            ground_truth.append(
                {
                    "impact_id": f"IMP-{counter:03d}",

                    "regulatory_change_id": change_id,

                    "regulatory_act": change[
                        "regulatory_act"
                    ],

                    "change_topic": change[
                        "change_topic"
                    ],

                    "affected_policy_id": policy_id,

                    "relationship_type": (
                        relationship_type
                    ),

                    "impact_type": impact_type,

                    "expected_action": (
                        get_expected_action(
                            relationship_type
                        )
                    ),

                    "impact_status": (
                        get_impact_status(
                            relationship_type
                        )
                    ),

                    "evidence_policy_version": (
                        get_evidence_version(
                            policy_id,
                            relationship_type
                        )
                    ),

                    "ground_truth_source": (
                        "synthetic_evaluation_mapping"
                    ),

                    "synthetic": True,
                }
            )

            counter += 1

    return ground_truth


# ============================================================
# 9. SAVE JSON
# ============================================================

def save_json(
    filename,
    data
):

    output_path = OUTPUT_DIR / filename

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Created: {output_path}"
    )


# ============================================================
# 10. VALIDATE DISTRIBUTION
# ============================================================

def validate_ground_truth(
    ground_truth
):

    counts = {
        "direct": 0,
        "indirect": 0,
        "no_impact": 0,
    }

    for record in ground_truth:

        relationship = record[
            "relationship_type"
        ]

        if relationship not in counts:
            raise ValueError(
                f"Unexpected relationship: {relationship}"
            )

        counts[relationship] += 1

    expected = {
        "direct": 30,
        "indirect": 30,
        "no_impact": 30,
    }

    if counts != expected:

        raise ValueError(
            f"Distribution validation failed.\n"
            f"Expected: {expected}\n"
            f"Actual: {counts}"
        )

    # Verify every scenario has exactly
    # 2 direct + 2 indirect + 2 no-impact.

    for change in REGULATORY_CHANGES:

        change_id = change[
            "regulatory_change_id"
        ]

        scenario_records = [
            record
            for record in ground_truth
            if record["regulatory_change_id"]
            == change_id
        ]

        if len(scenario_records) != 6:

            raise ValueError(
                f"{change_id} has "
                f"{len(scenario_records)} records. "
                f"Expected 6."
            )

        scenario_counts = {
            "direct": 0,
            "indirect": 0,
            "no_impact": 0,
        }

        for record in scenario_records:

            relationship = record[
                "relationship_type"
            ]

            scenario_counts[
                relationship
            ] += 1

        if scenario_counts != {
            "direct": 2,
            "indirect": 2,
            "no_impact": 2,
        }:

            raise ValueError(
                f"{change_id} distribution invalid: "
                f"{scenario_counts}"
            )

    print()
    print(
        "Distribution validation: PASSED"
    )


# ============================================================
# 11. SUMMARY
# ============================================================

def print_summary(
    policy_versions,
    relationships,
    ground_truth
):

    from collections import Counter

    relationship_counts = Counter(
        item["relationship_type"]
        for item in ground_truth
    )

    impact_counts = Counter(
        item["impact_type"]
        for item in ground_truth
    )

    action_counts = Counter(
        item["expected_action"]
        for item in ground_truth
    )

    print()
    print("=" * 60)
    print(
        "UPGRADED SYNTHETIC POLICY DATASET"
    )
    print("=" * 60)

    print(
        f"Policies              : {len(POLICIES)}"
    )

    print(
        f"Policy versions       : "
        f"{len(policy_versions)}"
    )

    print(
        f"Regulatory scenarios  : "
        f"{len(REGULATORY_CHANGES)}"
    )

    print(
        f"Policy relationships  : "
        f"{len(relationships)}"
    )

    print(
        f"Impact records        : "
        f"{len(ground_truth)}"
    )

    print()
    print("Relationship distribution")
    print("-" * 40)

    print(
        f"Direct                : "
        f"{relationship_counts['direct']}"
    )

    print(
        f"Indirect              : "
        f"{relationship_counts['indirect']}"
    )

    print(
        f"No impact             : "
        f"{relationship_counts['no_impact']}"
    )

    print()
    print("Impact type distribution")
    print("-" * 40)

    for key, value in impact_counts.items():
        print(
            f"{key:<22}: {value}"
        )

    print()
    print("Expected action distribution")
    print("-" * 40)

    for key, value in action_counts.items():
        print(
            f"{key:<22}: {value}"
        )

    print()
    print(
        f"Output directory:\n{OUTPUT_DIR}"
    )

    print("=" * 60)


# ============================================================
# 12. MAIN
# ============================================================

def main():

    print()
    print(
        "Generating balanced synthetic "
        "policy dataset..."
    )

    policy_versions = (
        generate_policy_versions()
    )

    policy_relationships = (
        generate_policy_relationships()
    )

    ground_truth = (
        generate_ground_truth()
    )

    # --------------------------------------------------------
    # VALIDATE BEFORE WRITING FILES
    # --------------------------------------------------------

    validate_ground_truth(
        ground_truth
    )

    # --------------------------------------------------------
    # Add synthetic marker to policies
    # --------------------------------------------------------

    policies_output = []

    for policy in POLICIES:

        policy_copy = dict(policy)

        policy_copy["synthetic"] = True

        policies_output.append(
            policy_copy
        )

    # --------------------------------------------------------
    # Add synthetic marker to regulatory changes
    # --------------------------------------------------------

    regulatory_changes_output = []

    for change in REGULATORY_CHANGES:

        change_copy = dict(change)

        change_copy["synthetic"] = True

        regulatory_changes_output.append(
            change_copy
        )

    # --------------------------------------------------------
    # Save files
    # --------------------------------------------------------

    save_json(
        "policies.json",
        policies_output
    )

    save_json(
        "policy_versions.json",
        policy_versions
    )

    save_json(
        "regulatory_changes.json",
        regulatory_changes_output
    )

    save_json(
        "policy_relationships.json",
        policy_relationships
    )

    save_json(
        "impact_ground_truth.json",
        ground_truth
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print_summary(
        policy_versions,
        policy_relationships,
        ground_truth
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()