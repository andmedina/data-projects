# Stakeholder Summary — Emergency Department Activity

The Phase 1 dashboard can show monthly completed ED encounters, unique patients with ED activity, and repeat-use intensity. The figures are generated from synthetic FHIR data and are suitable for demonstrating pipeline behavior, reconciliation, and dashboard design.

In the validated local snapshot, 68 completed ED encounters were distributed across 12 months. Each monthly encounter count reconciled exactly to the canonical encounter table, and no qualifying encounter lacked a reporting timestamp.

The current result should not be labeled an ED utilization rate. It describes only patients who used the ED; it does not yet include an eligible member-month denominator. It also should not be used for facility comparisons because encounter locations are not modeled in this phase.

Before production use, the team would validate source-specific encounter-class mappings, enrollment eligibility, facility attribution, time-zone rules, demographic completeness, late-arriving records, and suppression requirements with clinical, compliance, and operations stakeholders.
