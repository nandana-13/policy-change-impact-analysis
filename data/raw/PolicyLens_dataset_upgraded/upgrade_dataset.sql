-- PolicyLens dataset upgrade
-- Preserves existing policy IDs, version IDs and regulatory-change IDs.
-- Run from the project backend environment after backing up the database.

BEGIN;

UPDATE policies SET description='This policy governs how the organisation collects, uses, stores, shares and disposes of personal information relating to employees, contractors, interns and job applicants. HR must collect only information required for legitimate employment, payroll, benefits, safeguarding and legal purposes. Access is restricted to authorised personnel based on role and business need.

Employee records containing personal or sensitive information must be stored in approved systems, protected against unauthorised access, and reviewed periodically for accuracy and retention. Transfers to third parties require an approved contractual or legal basis. HR must maintain records of processing activities, access permissions and material disclosures where required. Requests concerning access, correction or deletion of personal information must be routed through the designated privacy process.' WHERE policy_id='POL-001';
UPDATE policies SET description='This policy establishes requirements for protecting customer personal information throughout its lifecycle. Business and technology teams must identify the categories of customer data they collect, the purpose for processing, authorised users, approved systems and permitted disclosures. Personal information must be protected using appropriate access controls, encryption and secure transmission mechanisms.

Customer data may be shared with processors or service providers only after the required security, privacy and contractual checks have been completed. Systems handling customer information must maintain access logs and support incident investigation. Material privacy incidents must be escalated to the privacy and information-security functions so that notification, containment and remediation obligations can be assessed.' WHERE policy_id='POL-002';
UPDATE policies SET description='This policy defines how long organisational records and information are retained, reviewed and securely disposed of. Retention periods are determined by record type, legal or regulatory requirements, contractual obligations and legitimate business needs. Records subject to a legal hold, investigation or audit must not be destroyed until the hold is formally released.

System owners are responsible for maintaining retention schedules and implementing appropriate deletion or archival controls. Periodic reviews must identify records that have exceeded their approved retention period. Disposal must use approved secure deletion, destruction or anonymisation procedures, and evidence of disposal must be retained where required.' WHERE policy_id='POL-003';
UPDATE policies SET description='This policy defines the process for detecting, reporting, assessing, containing and resolving incidents involving personal, confidential or regulated information. Employees must promptly report suspected loss, unauthorised access, disclosure, alteration or destruction of protected information through the incident-management process.

The security team performs initial triage and coordinates with privacy, legal and business owners to determine the affected data, individuals, systems, jurisdictions and potential regulatory obligations. Incidents must be documented from detection through closure, including decisions, evidence, containment actions and corrective measures. Notification decisions must be based on applicable legal requirements and documented approval.' WHERE policy_id='POL-004';
UPDATE policies SET description='This policy requires employment decisions to be made fairly and consistently without unlawful discrimination. It applies to recruitment, promotion, compensation, training, performance management, disciplinary action and termination. Managers must use objective, job-related criteria and avoid decisions based on protected characteristics or other prohibited grounds.

HR is responsible for maintaining appropriate procedures for complaints and reviewing workforce practices for potential unequal outcomes. Recruitment and employment records must contain sufficient evidence to demonstrate that decisions followed approved criteria. Concerns about discriminatory treatment must be escalated through the grievance or HR investigation process and handled confidentially.' WHERE policy_id='POL-005';
UPDATE policies SET description='This policy establishes a controlled and consistent recruitment process from job approval through candidate selection and offer. Roles must have documented requirements, approved evaluation criteria and authorised hiring responsibility before recruitment begins. Candidate information must be collected only for legitimate recruitment purposes and handled through approved systems.

Interview and assessment outcomes must be recorded using standard evaluation criteria. Selection decisions should be supported by documented evidence and reviewed for consistency. Background checks, references and other screening activities must follow applicable legal and privacy requirements. Candidate records must be retained and disposed of according to the approved retention schedule.' WHERE policy_id='POL-006';
UPDATE policies SET description='This policy governs requests for reasonable workplace adjustments for employees and candidates. Requests must be received through an approved HR channel and assessed promptly, confidentially and individually. Managers must not request unnecessary medical or personal information and must involve the appropriate HR specialists when specialist assessment is required.

Approved adjustments may include changes to working arrangements, equipment, schedules, workspace or job processes. Decisions and implementation responsibilities must be documented without exposing sensitive information unnecessarily. HR must periodically review accommodation arrangements and ensure that employees are not disadvantaged for requesting or using an approved adjustment.' WHERE policy_id='POL-007';
UPDATE policies SET description='This policy provides a formal process for employees to raise concerns about workplace treatment, employment decisions, harassment, discrimination, policy breaches or other unresolved issues. Employees may submit grievances through designated channels, and managers must escalate matters that cannot be resolved informally.

Grievances must be acknowledged, assigned to an appropriate investigator and handled impartially. Relevant evidence, interviews and decisions must be documented. Employees must not be subject to retaliation for raising a legitimate concern. Case records must be access-controlled and retained according to the applicable HR retention schedule.' WHERE policy_id='POL-008';
UPDATE policies SET description='This policy establishes controls for preparing accurate, complete and timely financial reports. Finance teams must maintain supporting records for material transactions, perform reconciliations and apply approved accounting policies consistently. Journal entries, estimates and adjustments must have appropriate review and evidence of approval.

Financial reporting processes must include period-end controls, management review and segregation of duties for key activities. Material errors or suspected misstatements must be escalated promptly. Records supporting financial statements must be retained for the applicable statutory, audit and corporate retention periods.' WHERE policy_id='POL-009';
UPDATE policies SET description='This policy establishes requirements for identifying, calculating, documenting and meeting the organisation''s tax obligations. Finance must maintain a calendar of applicable filing and payment deadlines and assign responsibility for preparation, review and submission. Tax positions must be supported by appropriate records and reviewed when business activities or regulations change.

Tax records must be complete, traceable and retained for the required period. Material tax risks, uncertain positions and potential non-compliance must be escalated to the designated tax and finance leadership. External advisers may be used where specialist advice is required, subject to approved engagement and confidentiality controls.' WHERE policy_id='POL-010';
UPDATE policies SET description='This policy governs employee and business expense claims, approvals, reimbursement and supporting documentation. Claims must be submitted through approved systems within the prescribed period and must identify the business purpose, amount, date and required supporting evidence.

Managers are responsible for reviewing claims for legitimacy, policy compliance and appropriate business purpose. Finance performs additional checks and may reject unsupported or unusual transactions. Expenses involving related parties, gifts, travel or other controlled categories require the additional approvals specified by the relevant procedures. Records must be retained for financial, tax and audit purposes.' WHERE policy_id='POL-011';
UPDATE policies SET description='This policy defines the organisation''s framework for internal and external financial audit activities. Audit planning must consider financial reporting risks, materiality, prior findings, control effectiveness and changes to the organisation''s operating environment. Auditors must have appropriate access to records and must maintain independence from activities they assess.

Audit evidence, findings, management responses and remediation status must be documented. Significant control deficiencies or suspected financial misconduct must be escalated to the appropriate governance body. Corrective actions must have accountable owners and target dates, and unresolved high-risk findings must remain visible through subsequent review cycles.' WHERE policy_id='POL-012';
UPDATE policies SET description='This policy establishes controls for calculating and processing employee payroll accurately and on time. Payroll must use approved employee, attendance, compensation, deduction and tax information. Changes to salary, bank details, benefits or deductions require authorised source documentation and appropriate review before inclusion in payroll.

Payroll calculations must undergo pre-processing validation and post-processing reconciliation. Exceptions must be investigated before final payment where practicable. Payroll records must be protected because they contain personal and financial information, and statutory deductions, reporting and record-retention requirements must be monitored by the payroll function.' WHERE policy_id='POL-013';
UPDATE policies SET description='This policy governs the administration of employee benefits, including eligibility, enrolment, changes, approvals and communication. Benefits must be administered according to approved plan terms and applicable employment requirements. HR and payroll must maintain accurate eligibility and deduction information and coordinate changes that affect compensation or employee records.

Benefit-related personal and financial information must be restricted to authorised personnel. Material changes to benefit plans must be communicated through approved channels and reflected in the relevant systems and records. Supporting documents must be retained according to legal, contractual and organisational requirements.' WHERE policy_id='POL-014';
UPDATE policies SET description='This policy establishes requirements for maintaining accurate records of employee compensation, salary changes, incentives, allowances, deductions and related approvals. Every material compensation change must be traceable to an authorised decision and recorded in the approved HR or payroll system.

Access to compensation records must be limited according to role. Payroll and HR must periodically reconcile compensation records against approved employee data and investigate discrepancies. Records must be retained for the applicable employment, tax, payroll and audit periods, with secure disposal after the retention requirement ends.' WHERE policy_id='POL-015';
UPDATE policies SET description='This policy defines controls for periodically reviewing payroll accuracy, compliance and operational effectiveness. Payroll audits may examine employee master data, salary changes, deductions, tax calculations, benefits, payment files, access rights and reconciliation evidence.

Audit testing must maintain an appropriate evidence trail and identify exceptions, control weaknesses and potential financial exposure. Findings must be assigned to accountable owners and tracked to closure. Access to payroll audit evidence must be restricted because the records may contain sensitive personal and financial information.' WHERE policy_id='POL-016';
UPDATE policies SET description='This policy governs procurement activities involving local suppliers, contractors and community-facing purchasing. Procurement decisions must follow approved sourcing, evaluation, approval and conflict-of-interest controls. Where local supplier participation or local procurement requirements apply, the responsible team must maintain evidence demonstrating how the requirement was assessed and satisfied.

Supplier records, quotations, evaluations, approvals and contracts must be retained in the approved procurement system. Exceptions to standard procurement procedures require documented justification and authorised approval. Procurement teams must monitor changes in applicable local requirements and update procedures when obligations change.' WHERE policy_id='POL-017';
UPDATE policies SET description='This policy establishes controls for property-related planning, permits, development activity and engagement with local authorities. Facilities teams must identify applicable planning, property and local approval requirements before commencing controlled activities. Required permits, approvals, correspondence and supporting technical documents must be stored in the designated records system.

Changes to property use, construction activity or site arrangements must be reviewed for regulatory implications. Engagement with local authorities must be documented, including submissions, decisions, conditions and follow-up actions. Records must be retained so that the organisation can demonstrate compliance during audits or regulatory enquiries.' WHERE policy_id='POL-018';
UPDATE policies SET description='This policy establishes a structured approach for engaging local communities and other external stakeholders affected by organisational activities. Engagement activities must identify relevant stakeholders, define the purpose of consultation and provide appropriate channels for receiving and recording feedback.

Material concerns, commitments and responses must be documented and assigned to responsible teams. Where community engagement is required by a permit, planning condition or other obligation, the relevant evidence must be maintained with the associated project records. Public communications must be accurate, approved and consistent with applicable legal and organisational requirements.' WHERE policy_id='POL-019';
UPDATE policies SET description='This policy establishes the organisation''s framework for identifying, assessing, monitoring and documenting local regulatory obligations. Compliance must maintain a register of applicable requirements, responsible owners, effective dates and required controls. Business functions must notify Compliance when new activities, locations or regulatory communications may create additional obligations.

Regulatory assessments must identify affected processes, records, approvals and reporting requirements. Material changes must be communicated to affected policy owners, and evidence of implementation must be retained. Compliance issues, missed obligations and unresolved regulatory risks must be escalated according to the organisation''s risk-management process.' WHERE policy_id='POL-020';
UPDATE policy_versions
SET effective_date='2025-02-15',
    change_description='Baseline policy establishes authorised collection, access control, retention and incident-escalation requirements for employee information.',
    status='superseded'
WHERE policy_version_id='POL-001-V1';
UPDATE policy_versions
SET effective_date='2026-02-15',
    change_description='Version 2 introduces documented processing-purpose reviews, stronger third-party disclosure controls and mandatory periodic access reviews.',
    status='superseded'
WHERE policy_version_id='POL-001-V2';
UPDATE policy_versions
SET effective_date='2027-02-15',
    change_description='Version 3 adds formal evidence requirements for privacy requests, transfer assessments and incident-notification decisions.',
    status='active'
WHERE policy_version_id='POL-001-V3';
UPDATE policy_versions
SET effective_date='2025-03-15',
    change_description='Baseline policy establishes lifecycle controls for customer personal information and approved-system requirements.',
    status='superseded'
WHERE policy_version_id='POL-002-V1';
UPDATE policy_versions
SET effective_date='2026-03-15',
    change_description='Version 2 strengthens processor due diligence, access logging and security requirements for systems handling customer information.',
    status='superseded'
WHERE policy_version_id='POL-002-V2';
UPDATE policy_versions
SET effective_date='2027-03-15',
    change_description='Version 3 adds formal privacy-incident escalation criteria and documented assessment of notification obligations.',
    status='active'
WHERE policy_version_id='POL-002-V3';
UPDATE policy_versions
SET effective_date='2025-04-15',
    change_description='Baseline policy establishes retention schedules, legal-hold controls and secure disposal requirements.',
    status='superseded'
WHERE policy_version_id='POL-003-V1';
UPDATE policy_versions
SET effective_date='2026-04-15',
    change_description='Version 2 introduces periodic retention reviews and owner accountability for overdue records.',
    status='superseded'
WHERE policy_version_id='POL-003-V2';
UPDATE policy_versions
SET effective_date='2027-04-15',
    change_description='Version 3 strengthens evidence of deletion, archival and legal-hold release decisions.',
    status='active'
WHERE policy_version_id='POL-003-V3';
UPDATE policy_versions
SET effective_date='2025-05-15',
    change_description='Baseline policy establishes reporting, triage, containment and documentation requirements for data incidents.',
    status='superseded'
WHERE policy_version_id='POL-004-V1';
UPDATE policy_versions
SET effective_date='2026-05-15',
    change_description='Version 2 adds formal severity classification and mandatory coordination between security, privacy and legal teams.',
    status='superseded'
WHERE policy_version_id='POL-004-V2';
UPDATE policy_versions
SET effective_date='2027-05-15',
    change_description='Version 3 strengthens incident evidence, notification-decision records and post-incident corrective-action tracking.',
    status='active'
WHERE policy_version_id='POL-004-V3';
UPDATE policy_versions
SET effective_date='2025-06-15',
    change_description='Baseline policy establishes non-discrimination and fair-decision principles across employment activities.',
    status='superseded'
WHERE policy_version_id='POL-005-V1';
UPDATE policy_versions
SET effective_date='2026-06-15',
    change_description='Version 2 adds documented objective selection criteria and periodic review of employment decision processes.',
    status='superseded'
WHERE policy_version_id='POL-005-V2';
UPDATE policy_versions
SET effective_date='2027-06-15',
    change_description='Version 3 strengthens complaint escalation, investigation records and monitoring of potential unequal outcomes.',
    status='active'
WHERE policy_version_id='POL-005-V3';
UPDATE policy_versions
SET effective_date='2025-07-15',
    change_description='Baseline policy establishes standard recruitment, assessment, screening and candidate-record requirements.',
    status='superseded'
WHERE policy_version_id='POL-006-V1';
UPDATE policy_versions
SET effective_date='2026-07-15',
    change_description='Version 2 introduces documented evaluation criteria and additional review of screening and candidate-data handling.',
    status='superseded'
WHERE policy_version_id='POL-006-V2';
UPDATE policy_versions
SET effective_date='2027-07-15',
    change_description='Version 3 strengthens retention, access control and evidence requirements for recruitment decisions.',
    status='active'
WHERE policy_version_id='POL-006-V3';
UPDATE policy_versions
SET effective_date='2025-08-15',
    change_description='Baseline policy establishes confidential assessment and implementation of reasonable workplace adjustments.',
    status='superseded'
WHERE policy_version_id='POL-007-V1';
UPDATE policy_versions
SET effective_date='2026-08-15',
    change_description='Version 2 introduces formal request tracking, specialist review and implementation ownership.',
    status='superseded'
WHERE policy_version_id='POL-007-V2';
UPDATE policy_versions
SET effective_date='2027-08-15',
    change_description='Version 3 strengthens confidentiality controls and periodic review of accommodation arrangements.',
    status='active'
WHERE policy_version_id='POL-007-V3';
UPDATE policy_versions
SET effective_date='2025-09-15',
    change_description='Baseline policy establishes formal submission, investigation and resolution procedures for employee grievances.',
    status='superseded'
WHERE policy_version_id='POL-008-V1';
UPDATE policy_versions
SET effective_date='2026-09-15',
    change_description='Version 2 adds mandatory acknowledgement, investigator assignment and evidence-retention requirements.',
    status='superseded'
WHERE policy_version_id='POL-008-V2';
UPDATE policy_versions
SET effective_date='2027-09-15',
    change_description='Version 3 strengthens anti-retaliation controls, confidentiality and management reporting for unresolved cases.',
    status='active'
WHERE policy_version_id='POL-008-V3';
UPDATE policy_versions
SET effective_date='2025-10-15',
    change_description='Baseline policy establishes financial reporting preparation, reconciliation, review and supporting-record requirements.',
    status='superseded'
WHERE policy_version_id='POL-009-V1';
UPDATE policy_versions
SET effective_date='2026-10-15',
    change_description='Version 2 strengthens journal-entry approval, period-end controls and material-error escalation.',
    status='superseded'
WHERE policy_version_id='POL-009-V2';
UPDATE policy_versions
SET effective_date='2027-10-15',
    change_description='Version 3 adds enhanced evidence requirements for estimates, adjustments and audit support.',
    status='active'
WHERE policy_version_id='POL-009-V3';
UPDATE policy_versions
SET effective_date='2025-11-15',
    change_description='Baseline policy establishes tax filing, payment, documentation and ownership requirements.',
    status='superseded'
WHERE policy_version_id='POL-010-V1';
UPDATE policy_versions
SET effective_date='2026-11-15',
    change_description='Version 2 introduces a controlled tax calendar and formal review of material tax positions.',
    status='superseded'
WHERE policy_version_id='POL-010-V2';
UPDATE policy_versions
SET effective_date='2027-11-15',
    change_description='Version 3 strengthens retention, adviser oversight and escalation of uncertain or potentially non-compliant tax positions.',
    status='active'
WHERE policy_version_id='POL-010-V3';
UPDATE policy_versions
SET effective_date='2025-12-15',
    change_description='Baseline policy establishes expense submission, approval, reimbursement and supporting-document requirements.',
    status='superseded'
WHERE policy_version_id='POL-011-V1';
UPDATE policy_versions
SET effective_date='2026-12-15',
    change_description='Version 2 strengthens manager review and controls for unusual, related-party and controlled-category expenses.',
    status='superseded'
WHERE policy_version_id='POL-011-V2';
UPDATE policy_versions
SET effective_date='2027-12-15',
    change_description='Version 3 adds enhanced evidence and audit-trail requirements for expense exceptions and rejected claims.',
    status='active'
WHERE policy_version_id='POL-011-V3';
UPDATE policy_versions
SET effective_date='2025-01-15',
    change_description='Baseline policy establishes audit planning, evidence, findings and remediation controls.',
    status='superseded'
WHERE policy_version_id='POL-012-V1';
UPDATE policy_versions
SET effective_date='2026-01-15',
    change_description='Version 2 introduces risk-based audit planning and stronger governance escalation for significant control deficiencies.',
    status='superseded'
WHERE policy_version_id='POL-012-V2';
UPDATE policy_versions
SET effective_date='2027-01-15',
    change_description='Version 3 strengthens remediation tracking, evidence retention and follow-up of unresolved high-risk findings.',
    status='active'
WHERE policy_version_id='POL-012-V3';
UPDATE policy_versions
SET effective_date='2025-02-15',
    change_description='Baseline policy establishes payroll calculation, approval, validation, reconciliation and statutory reporting controls.',
    status='superseded'
WHERE policy_version_id='POL-013-V1';
UPDATE policy_versions
SET effective_date='2026-02-15',
    change_description='Version 2 strengthens controls over employee-master changes, bank details and compensation inputs.',
    status='superseded'
WHERE policy_version_id='POL-013-V2';
UPDATE policy_versions
SET effective_date='2027-02-15',
    change_description='Version 3 adds enhanced pre-payment validation, exception tracking and payroll-record access controls.',
    status='active'
WHERE policy_version_id='POL-013-V3';
UPDATE policy_versions
SET effective_date='2025-03-15',
    change_description='Baseline policy establishes employee-benefit eligibility, enrolment, administration and recordkeeping requirements.',
    status='superseded'
WHERE policy_version_id='POL-014-V1';
UPDATE policy_versions
SET effective_date='2026-03-15',
    change_description='Version 2 strengthens coordination between HR and payroll for benefit-related compensation and deduction changes.',
    status='superseded'
WHERE policy_version_id='POL-014-V2';
UPDATE policy_versions
SET effective_date='2027-03-15',
    change_description='Version 3 adds formal communication and evidence requirements for material benefit-plan changes.',
    status='active'
WHERE policy_version_id='POL-014-V3';
UPDATE policy_versions
SET effective_date='2025-04-15',
    change_description='Baseline policy establishes traceable records for compensation, salary changes, incentives, deductions and approvals.',
    status='superseded'
WHERE policy_version_id='POL-015-V1';
UPDATE policy_versions
SET effective_date='2026-04-15',
    change_description='Version 2 introduces periodic reconciliation between compensation records and approved HR data.',
    status='superseded'
WHERE policy_version_id='POL-015-V2';
UPDATE policy_versions
SET effective_date='2027-04-15',
    change_description='Version 3 strengthens access restrictions, discrepancy escalation and retention controls for compensation records.',
    status='active'
WHERE policy_version_id='POL-015-V3';
UPDATE policy_versions
SET effective_date='2025-05-15',
    change_description='Baseline policy establishes payroll audit scope, evidence, exception reporting and remediation requirements.',
    status='superseded'
WHERE policy_version_id='POL-016-V1';
UPDATE policy_versions
SET effective_date='2026-05-15',
    change_description='Version 2 expands audit testing to access rights, payment files and reconciliation controls.',
    status='superseded'
WHERE policy_version_id='POL-016-V2';
UPDATE policy_versions
SET effective_date='2027-05-15',
    change_description='Version 3 strengthens finding ownership, closure evidence and protection of sensitive payroll audit records.',
    status='active'
WHERE policy_version_id='POL-016-V3';
UPDATE policy_versions
SET effective_date='2025-06-15',
    change_description='Baseline policy establishes sourcing, evaluation, approval and recordkeeping controls for local procurement.',
    status='superseded'
WHERE policy_version_id='POL-017-V1';
UPDATE policy_versions
SET effective_date='2026-06-15',
    change_description='Version 2 adds documented assessment of local supplier and local procurement requirements.',
    status='superseded'
WHERE policy_version_id='POL-017-V2';
UPDATE policy_versions
SET effective_date='2027-06-15',
    change_description='Version 3 strengthens exception approval, supplier evidence and monitoring of changes in local procurement obligations.',
    status='active'
WHERE policy_version_id='POL-017-V3';
UPDATE policy_versions
SET effective_date='2025-07-15',
    change_description='Baseline policy establishes controls for property approvals, planning requirements, authority engagement and records.',
    status='superseded'
WHERE policy_version_id='POL-018-V1';
UPDATE policy_versions
SET effective_date='2026-07-15',
    change_description='Version 2 introduces formal pre-activity regulatory checks and approval tracking.',
    status='superseded'
WHERE policy_version_id='POL-018-V2';
UPDATE policy_versions
SET effective_date='2027-07-15',
    change_description='Version 3 strengthens documentation of authority correspondence, conditions, permits and follow-up actions.',
    status='active'
WHERE policy_version_id='POL-018-V3';
UPDATE policy_versions
SET effective_date='2025-08-15',
    change_description='Baseline policy establishes structured stakeholder identification, consultation and engagement records.',
    status='superseded'
WHERE policy_version_id='POL-019-V1';
UPDATE policy_versions
SET effective_date='2026-08-15',
    change_description='Version 2 introduces formal tracking of community concerns, commitments and responsible owners.',
    status='superseded'
WHERE policy_version_id='POL-019-V2';
UPDATE policy_versions
SET effective_date='2027-08-15',
    change_description='Version 3 strengthens evidence requirements where engagement forms part of a regulatory or planning obligation.',
    status='active'
WHERE policy_version_id='POL-019-V3';
UPDATE policy_versions
SET effective_date='2025-09-15',
    change_description='Baseline policy establishes a regulatory register, ownership model and monitoring process for local obligations.',
    status='superseded'
WHERE policy_version_id='POL-020-V1';
UPDATE policy_versions
SET effective_date='2026-09-15',
    change_description='Version 2 introduces formal impact assessments for new requirements and escalation of material compliance gaps.',
    status='superseded'
WHERE policy_version_id='POL-020-V2';
UPDATE policy_versions
SET effective_date='2027-09-15',
    change_description='Version 3 strengthens evidence of implementation, effective-date tracking and communication to affected policy owners.',
    status='active'
WHERE policy_version_id='POL-020-V3';
UPDATE regulatory_changes
SET change_topic='Personal data processing and accountability',
    change_description='Introduces strengthened organisational expectations around documented processing purposes, access controls and evidence supporting the handling of personal information.'
WHERE regulatory_change_id='DATA_PROTECTION_ACT_2018-CHANGE-001';
UPDATE regulatory_changes
SET change_topic='Personal data retention and disposal',
    change_description='Clarifies requirements for retention schedules, review of unnecessary personal data and secure disposal after applicable retention periods.'
WHERE regulatory_change_id='DATA_PROTECTION_ACT_2018-CHANGE-002';
UPDATE regulatory_changes
SET change_topic='Personal data incident response',
    change_description='Strengthens expectations for documenting personal-data incidents, assessing risk and maintaining evidence supporting notification decisions.'
WHERE regulatory_change_id='DATA_PROTECTION_ACT_2018-CHANGE-003';
UPDATE regulatory_changes
SET change_topic='Equality in employment decisions',
    change_description='Clarifies requirements for consistent and non-discriminatory employment practices across recruitment, promotion and workplace decisions.'
WHERE regulatory_change_id='EQUALITY_ACT_2010-CHANGE-001';
UPDATE regulatory_changes
SET change_topic='Workplace adjustments',
    change_description='Strengthens expectations for considering reasonable workplace adjustments and documenting decisions without unnecessary disclosure of sensitive information.'
WHERE regulatory_change_id='EQUALITY_ACT_2010-CHANGE-002';
UPDATE regulatory_changes
SET change_topic='Employment records and grievance handling',
    change_description='Introduces stronger expectations for evidence, complaint handling and retention of records supporting fair employment practices.'
WHERE regulatory_change_id='EQUALITY_ACT_2010-CHANGE-003';
UPDATE regulatory_changes
SET change_topic='Financial reporting controls',
    change_description='Strengthens requirements affecting financial records, reporting evidence and controls supporting accurate financial information.'
WHERE regulatory_change_id='FINANCE_ACT_2003-CHANGE-001';
UPDATE regulatory_changes
SET change_topic='Tax records and reporting',
    change_description='Clarifies requirements for maintaining supporting tax records and ensuring timely, traceable reporting and payment processes.'
WHERE regulatory_change_id='FINANCE_ACT_2003-CHANGE-002';
UPDATE regulatory_changes
SET change_topic='Financial audit evidence',
    change_description='Strengthens expectations for audit evidence, review trails and retention of records supporting financial compliance.'
WHERE regulatory_change_id='FINANCE_ACT_2003-CHANGE-003';
UPDATE regulatory_changes
SET change_topic='Employment income and payroll records',
    change_description='Introduces changes affecting the calculation, reporting and evidencing of employment income and payroll-related obligations.'
WHERE regulatory_change_id='INCOME_TAX_EARNINGS_PENSIONS_ACT_2003-CHANGE-001';
UPDATE regulatory_changes
SET change_topic='Employee benefits and taxable compensation',
    change_description='Clarifies treatment and documentation requirements for employee benefits and compensation-related information used for tax purposes.'
WHERE regulatory_change_id='INCOME_TAX_EARNINGS_PENSIONS_ACT_2003-CHANGE-002';
UPDATE regulatory_changes
SET change_topic='Payroll compliance evidence',
    change_description='Strengthens expectations for maintaining payroll records and evidence supporting employment-income calculations and reporting.'
WHERE regulatory_change_id='INCOME_TAX_EARNINGS_PENSIONS_ACT_2003-CHANGE-003';
UPDATE regulatory_changes
SET change_topic='Local planning and community requirements',
    change_description='Introduces changes affecting local planning, community participation and organisational engagement with local authorities and stakeholders.'
WHERE regulatory_change_id='LOCALISM_ACT_2011-CHANGE-001';
UPDATE regulatory_changes
SET change_topic='Local procurement and community participation',
    change_description='Clarifies expectations relevant to local participation, procurement processes and evidence supporting local governance decisions.'
WHERE regulatory_change_id='LOCALISM_ACT_2011-CHANGE-002';
UPDATE regulatory_changes
SET change_topic='Local regulatory monitoring and records',
    change_description='Strengthens requirements for documenting local regulatory obligations, decisions, consultations and evidence of compliance.'
WHERE regulatory_change_id='LOCALISM_ACT_2011-CHANGE-003';

COMMIT;

-- Validation
SELECT COUNT(*) AS policies FROM policies;
SELECT COUNT(*) AS policy_versions FROM policy_versions;
SELECT COUNT(*) AS regulatory_changes FROM regulatory_changes;
SELECT COUNT(*) AS relationships FROM policy_relationships;
SELECT COUNT(*) AS impact_ground_truth FROM impact_ground_truth;
