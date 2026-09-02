# FHIR Mapping — Phase 1

| FHIR resource | Core purpose | Required source identifiers | Key relationships |
| --- | --- | --- | --- |
| `Patient` | person receiving care | `id`; available business identifiers | referenced by Encounter and Observation subject |
| `Encounter` | care interaction | `id`, subject reference, encounter period | references Patient; may reference Organization and Practitioner |
| `Observation` | typed measurement or clinical observation | `id`, status, subject reference, effective date/time when present | references Patient and may reference Encounter; retains category, `value[x]`, units, and absent reason |
| `Condition` | patient clinical condition | `id`, subject reference, clinical status, coding | may reference Patient and Encounter |
| `Procedure` | performed clinical procedure | `id`, subject reference, status, coding | may reference Patient and Encounter |
| `MedicationRequest` | medication order/request | `id`, subject reference, status, medication coding | may reference Patient and Encounter |
| `Organization` | provider or payer organization | `id`, name, type when present | referenced by Coverage payor |
| `Practitioner` | provider identity | `id`, name when present | available for future Encounter/Procedure attribution |
| `Coverage` | patient coverage relationship and eligibility period | `id`, status, beneficiary reference, payor reference, period start/end | references Patient and Organization; supplies payer member months |
| `ImagingStudy` | metadata-only imaging study and series | `id`, status, subject, started time, series UID/modality | references Patient and optionally Encounter; retains DICOM UID/modality and body-site metadata without pixels |

## Coding extraction

Where a CodeableConcept is present, transformations retain the coding system, code, and display. For Observations, LOINC coding is preferred when supplied but no coding system is inferred when it is absent.

## Value handling

Observation value types are explicitly classified. `valueQuantity` and `valueInteger` populate `value_numeric`; `valueString` populates `value_text`; `valueBoolean` populates `value_boolean`; and `valueCodeableConcept` retains its system, code, and display. Quantity unit, system, and code are stored separately so UCUM identity is not lost. `dataAbsentReason` remains distinct from an unexplained null result.

The first category coding identifies laboratory Observations for completeness monitoring. A final, amended, or corrected laboratory Observation must have a usable typed value or a documented absent reason. Multiple simultaneous FHIR `value[x]` choices and structurally invalid quantities are rejected before loading.

## Coverage period handling

The controlled Coverage profile requires both inclusive period boundaries. Core stores them as dates and rejects an end before its start. Active periods expand to every touched calendar month, then deduplicate patient/payer/month before aggregation. Partial months count as one member month and are not prorated.

## Incremental retrieval

FHIR REST retrieval requests use a persisted source/resource watermark as `_since`, follow only advertised `next` links, and save a new checkpoint only after a successful complete run. Payload hashes and source IDs remain the final idempotency guard because servers may return overlapping results.
