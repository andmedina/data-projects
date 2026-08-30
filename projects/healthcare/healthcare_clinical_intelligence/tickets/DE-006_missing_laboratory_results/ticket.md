# DE-006 — Missing Laboratory Results

## Incident

A final synthetic laboratory Observation reached the platform without a result value or a FHIR `dataAbsentReason`. The platform must distinguish an incomplete source record from a transformation that discarded the result, stop downstream publication, retain the source versions, and demonstrate recovery from a corrected later payload.

## Acceptance criteria

- [x] Preserve Observation category, typed `value[x]`, units, coded values, and absent-reason fields from raw through core.
- [x] Support Quantity, String, Boolean, Integer, and CodeableConcept result types without conflation.
- [x] Persist a critical missing-result control and a critical missing-effective-time control.
- [x] Fail the quality gate for a final laboratory result with neither value nor documented absent reason.
- [x] Retain both missing and corrected raw source versions.
- [x] Select the corrected later source version and update the canonical record idempotently.
- [x] Publish independently reconciled monthly lab-result completeness.
- [x] Document root cause, correction, validation, and prevention.

Status: complete for the reproducible synthetic incident.
