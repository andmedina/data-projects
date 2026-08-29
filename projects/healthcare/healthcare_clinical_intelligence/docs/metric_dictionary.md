# Metric Dictionary

## Emergency department utilization rate

**Status:** planned for Phase 1.

**Business question:** Which populations have the highest ED utilization?

**Numerator:** encounters classified as emergency encounters during the reporting period.

**Denominator:** distinct eligible patients with active records during the reporting period. The final eligibility rule and FHIR encounter classification mapping will be documented with the mart.

**Grain:** patient × reporting period, with rollups by facility and demographic attributes where available.

**Validation:** independently reconcile encounter counts to the core encounter model and verify that the cohort denominator follows the documented eligibility rule.
