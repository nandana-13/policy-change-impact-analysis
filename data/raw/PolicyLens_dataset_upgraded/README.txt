# PolicyLens Dataset Upgrade

This upgrade makes the existing synthetic company-policy dataset substantially richer while preserving the existing identifiers and database relationships.

Files:
- policies_upgraded.json — 20 richer policy descriptions
- policy_versions_upgraded.json — 60 meaningful version histories
- regulatory_changes_upgraded.json — 15 richer regulatory-change records
- upgrade_dataset.sql — database update script

Important:
- Existing policy IDs POL-001 through POL-020 are preserved.
- Existing version IDs POL-XXX-V1 through POL-XXX-V3 are preserved.
- Existing regulatory-change IDs are preserved.
- Existing policy relationships and impact-ground-truth rows are NOT deleted or recreated.
- The records remain synthetic and should be labelled as synthetic in the final product.

Run:
psql -U postgres -d policy_impact_analysis -f upgrade_dataset.sql

Or execute the SQL in pgAdmin Query Tool.

Afterward, refresh the PolicyLens Admin Dashboard.
