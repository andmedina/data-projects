# FHIR Mapping — Phase 1

| FHIR resource | Core purpose | Required source identifiers | Key relationships |
| --- | --- | --- | --- |
| `Patient` | person receiving care | `id`; available business identifiers | referenced by Encounter and Observation subject |
| `Encounter` | care interaction | `id`, subject reference, encounter period | references Patient; may reference Organization and Practitioner |
| `Observation` | measurement or clinical observation | `id`, status, subject reference, effective date/time when present | references Patient and may reference Encounter |

## Coding extraction

Where a CodeableConcept is present, transformations retain the coding system, code, and display. For Observations, LOINC coding is preferred when supplied but no coding system is inferred when it is absent.

## Value handling

Observation value types are explicitly classified. Numeric values, coded values, text values, boolean values, and absent values must not be conflated. Unsupported structures are quarantined with a reason code rather than silently discarded.

## Incremental retrieval

FHIR REST retrieval requests use a persisted source/resource watermark as `_since`, follow only advertised `next` links, and save a new checkpoint only after a successful complete run. Payload hashes and source IDs remain the final idempotency guard because servers may return overlapping results.
