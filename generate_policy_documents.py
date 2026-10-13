import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

# IMPORTANT:
# We are now using the upgraded PolicyLens dataset.
DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "PolicyLens_dataset_upgraded"
)

POLICIES_FILE = DATA_DIR / "policies_upgraded.json"

VERSIONS_FILE = DATA_DIR / "policy_versions_upgraded.json"

OUTPUT_DIR = DATA_DIR / "documents"

MANIFEST_FILE = DATA_DIR / "document_manifest.json"


# ============================================================
# LOAD JSON
# ============================================================

def load_json(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"\nFile not found:\n{file_path}\n"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# EXTRACT RECORDS
# ============================================================

def extract_records(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        for key in [
            "data",
            "records",
            "policies",
            "policy_versions"
        ]:

            if key in data:

                if isinstance(data[key], list):
                    return data[key]

    raise ValueError(
        "Unsupported JSON structure."
    )


# ============================================================
# VERSION-SPECIFIC REQUIREMENTS
# ============================================================

def get_controls(category, version):

    if version == 1:

        return [
            "All activities covered by this policy must follow approved organizational procedures.",

            "Responsibilities for implementing this policy must be clearly assigned.",

            "Material decisions must be documented and supported by appropriate records.",

            "Access to policy-related information must be limited to personnel with a legitimate business need.",

            "Known exceptions must be documented and reported to the policy owner."
        ]

    elif version == 2:

        return [
            "Each material control must have a named control owner and defined review frequency.",

            "Decisions and control activities must have sufficient evidence to allow independent review.",

            "Access to policy-related information must be periodically reviewed and excessive access removed.",

            "Exceptions must document the reason, risk, approving authority, responsible owner, and review or expiry date.",

            "Control owners must retain evidence of completed reviews and corrective actions."
        ]

    else:

        return [
            "Control owners must periodically assess control effectiveness and document identified weaknesses.",

            "Management reporting must identify significant control failures, overdue actions, and recurring exceptions.",

            "Material decisions must have traceable evidence linking the decision, approval, supporting records, and implementation.",

            "Repeated control failures must trigger root-cause analysis and documented corrective action.",

            "Material unresolved risks must be escalated to the appropriate management or compliance forum."
        ]


# ============================================================
# BUILD POLICY DOCUMENT
# ============================================================

def build_document(policy, version):

    policy_id = policy["policy_id"]

    policy_name = policy["policy_name"]

    category = policy.get(
        "category",
        "General"
    )

    department = policy.get(
        "department",
        "Not specified"
    )

    description = policy.get(
        "description",
        "This policy establishes organizational requirements."
    )

    version_number = version["version_number"]

    version_id = version["policy_version_id"]

    effective_date = version["effective_date"]

    status = version["status"]

    change_description = version["change_description"]

    controls = get_controls(
        category,
        version_number
    )

    # --------------------------------------------------------
    # VERSION-SPECIFIC TEXT
    # --------------------------------------------------------

    if version_number == 1:

        exception_text = """
Exceptions must identify the affected requirement,
the reason for the exception, the responsible owner,
and the expected review date.

Material or unresolved exceptions must be escalated
to the policy owner.
"""

        monitoring_text = """
The policy owner must review this policy at least every
24 months or sooner when a material business or regulatory
change occurs.
"""

    elif version_number == 2:

        exception_text = """
Exceptions must identify the affected requirement,
business rationale, risk, approving authority,
responsible owner, compensating controls where applicable,
and expiry or review date.

Expired exceptions must be closed, formally renewed,
or escalated.
"""

        monitoring_text = """
The policy owner must review this policy at least annually
and after a material regulatory, process, system, or
organizational change.

The review must document the reviewer, review date,
findings, and resulting actions.
"""

    else:

        exception_text = """
Exceptions must identify the affected requirement,
risk assessment, business rationale, approving authority,
responsible owner, compensating controls, expiry date,
and closure evidence.

Overdue exceptions must be escalated according to severity.

Repeated or systemic exceptions must be assessed for
root cause and possible policy or process changes.
"""

        monitoring_text = """
The policy owner must review this policy at least annually
and whenever a material regulatory, operational, system,
or risk change is identified.

The review must consider:

- recurring exceptions
- control failures
- audit findings
- incidents
- regulatory developments
- operational changes
- overdue corrective actions

Material weaknesses must have an assigned corrective
action and documented closure.
"""

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    document = f"""# {policy_name}

**Policy ID:** {policy_id}

**Policy Version ID:** {version_id}

**Version:** V{version_number}

**Status:** {status}

**Category:** {category}

**Owner Department:** {department}

**Effective Date:** {effective_date}


## 1. Purpose

{description}

This policy establishes the minimum organizational
requirements necessary to ensure that activities within
its scope are performed consistently, responsibly,
and with appropriate documentation.


## 2. Scope

This policy applies to employees, managers, contractors,
process owners, systems, records, and business activities
that fall within the subject matter of this policy.

It applies to both manual and technology-supported
activities unless an approved exception has been documented.


## 3. Definitions

### Policy Requirement

A mandatory organizational requirement established by this policy.

### Control Owner

The person responsible for ensuring that a defined control
is implemented, reviewed, and supported by appropriate evidence.

### Exception

An approved deviation from a requirement of this policy.

### Control Evidence

Records or information demonstrating that a required control,
decision, review, or activity has been performed.


## 4. Policy Requirements

The organization must apply the following requirements:

"""

    for number, control in enumerate(
        controls,
        start=1
    ):

        document += (
            f"{number}. {control}\n"
        )

    document += f"""

## 5. Roles and Responsibilities

### Policy Owner

The {department} department is responsible for maintaining
this policy and coordinating periodic reviews.

The policy owner must ensure that material changes are
communicated to relevant personnel.

### Process Owners

Process owners must implement the requirements of this
policy within their operational processes.

They must maintain evidence demonstrating that required
controls are operating effectively.

### Managers

Managers must ensure that personnel understand and follow
applicable requirements.

Managers must escalate material exceptions, risks,
and control failures.

### Employees and Contractors

Employees and contractors must follow approved procedures
and report suspected non-compliance, incidents, or
control failures.
"""

    if version_number >= 2:

        document += """

### Control Owners

Control owners must complete scheduled control reviews
and retain evidence of review outcomes.

They must also record corrective actions arising from
control weaknesses.
"""

    if version_number >= 3:

        document += """

### Management and Assurance Functions

Management and relevant assurance functions must review
significant unresolved risks, recurring failures,
and overdue corrective actions.

Material weaknesses must be escalated through the
appropriate governance process.
"""

    document += """

## 6. Records and Evidence

The organization must maintain sufficient evidence
to demonstrate that this policy has been implemented.

Minimum evidence includes:

- Approved policy version and effective date.
- Required approvals and authorization records.
- Operational records demonstrating application of the policy.
- Exception records where applicable.
"""

    if version_number >= 2:

        document += """
- Periodic control review records.
- Corrective-action records.
"""

    if version_number >= 3:

        document += """
- Management reporting where applicable.
- Root-cause analysis for recurring failures.
- Corrective-action closure evidence.
"""

    document += """

Records must be stored in approved organizational systems.

Access to records must be restricted according to role
and business need.

Records must not be altered or destroyed in a manner that
prevents required investigation, audit, review, or
regulatory response.


## 7. Exceptions and Escalation

"""

    document += exception_text

    document += """

## 8. Monitoring and Review

"""

    document += monitoring_text

    if version_number >= 3:

        document += """
The policy owner must maintain evidence of completed reviews,
identified weaknesses, assigned corrective actions,
and closure status.

Management reporting must identify significant overdue
actions, recurring control failures, and unresolved
material risks.
"""

    document += f"""

## 9. Related Policies and Controls

This policy should be read together with applicable
organizational policies, procedures, information-security
controls, records-management requirements, compliance
controls, audit requirements, and operational procedures
relevant to its subject matter.


## 10. Version Change Summary

{change_description}


## 11. Document Control

| Field | Value |
|---|---|
| Policy ID | {policy_id} |
| Policy Version ID | {version_id} |
| Version | V{version_number} |
| Effective Date | {effective_date} |
| Status | {status} |
| Owner Department | {department} |
| Category | {category} |

---

**Document Type:** Synthetic enterprise policy for PolicyLens
development and evaluation.

**Notice:** This document is synthetic test data and is not
legal advice or an actual organizational policy.
"""

    return document


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("POLICYLENS POLICY DOCUMENT GENERATOR")
    print("=" * 60)

    print("\nDataset:")
    print(DATA_DIR)

    print("\nLoading policies...")

    policies_data = load_json(
        POLICIES_FILE
    )

    print("Loading policy versions...")

    versions_data = load_json(
        VERSIONS_FILE
    )

    policies = extract_records(
        policies_data
    )

    versions = extract_records(
        versions_data
    )

    print(
        f"\nPolicies loaded : {len(policies)}"
    )

    print(
        f"Versions loaded : {len(versions)}"
    )

    # --------------------------------------------------------
    # POLICY LOOKUP
    # --------------------------------------------------------

    policy_lookup = {
        policy["policy_id"]: policy
        for policy in policies
    }

    # --------------------------------------------------------
    # CREATE OUTPUT DIRECTORY
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    manifest = []

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    for version in versions:

        policy_id = version["policy_id"]

        if policy_id not in policy_lookup:

            print(
                f"WARNING: {policy_id} "
                f"not found in policies.json"
            )

            continue

        policy = policy_lookup[
            policy_id
        ]

        version_number = version[
            "version_number"
        ]

        document = build_document(
            policy,
            version
        )

        output_directory = (
            OUTPUT_DIR
            / policy_id
            / f"V{version_number}"
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            output_directory
            / "policy.md"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(document)

        manifest.append(
            {
                "policy_id": policy_id,

                "policy_name": policy[
                    "policy_name"
                ],

                "policy_version_id": version[
                    "policy_version_id"
                ],

                "version_number": version[
                    "version_number"
                ],

                "effective_date": version[
                    "effective_date"
                ],

                "status": version[
                    "status"
                ],

                "category": policy.get(
                    "category"
                ),

                "department": policy.get(
                    "department"
                ),

                "document_path": str(
                    output_file.relative_to(
                        DATA_DIR
                    )
                ).replace("\\", "/")
            }
        )

        print(
            f"Created "
            f"{policy_id}/V{version_number}/policy.md"
        )

    # --------------------------------------------------------
    # SAVE MANIFEST
    # --------------------------------------------------------

    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    generated_files = list(
        OUTPUT_DIR.rglob(
            "policy.md"
        )
    )

    print()
    print("=" * 60)
    print("VALIDATION")
    print("=" * 60)

    print(
        f"Expected documents : {len(versions)}"
    )

    print(
        f"Generated documents: {len(generated_files)}"
    )

    if len(generated_files) == len(versions):

        print(
            "\nSUCCESS!"
        )

        print(
            "All policy documents were generated."
        )

    else:

        print(
            "\nWARNING!"
        )

        print(
            "Generated document count does not "
            "match policy version count."
        )

    print()
    print(
        "Documents location:"
    )

    print(
        OUTPUT_DIR
    )

    print()
    print(
        "Manifest:"
    )

    print(
        MANIFEST_FILE
    )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()