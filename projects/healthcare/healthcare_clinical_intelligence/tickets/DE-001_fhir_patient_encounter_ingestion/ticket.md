# DE-001 — FHIR Patient and Encounter Ingestion

## Business context

Clinical analytics needs a reliable daily feed of patient and encounter data from the synthetic EHR source.

## Problem statement

There is no repeatable process that retrieves or reads FHIR `Patient` and `Encounter` resources, preserves source fidelity, and makes load outcomes auditable.

## Acceptance criteria

- The pipeline reads Synthea FHIR R4 resources and can support paginated HAPI FHIR retrieval.
- Each resource is persisted in the raw layer with source metadata and the original JSON.
- Rerunning unchanged input does not duplicate raw records.
- Unsupported or malformed resources are quarantined with a reason code.
- A run report shows source, loaded, skipped, and rejected counts by resource type.
- Automated tests cover required identifiers and idempotency behavior.

## Constraints

- Synthetic data only.
- No rejected record may disappear silently.
- Raw payloads must be sufficient for replay and diagnosis.

## Planned evidence

- ingestion implementation and tests
- sample run report
- source-to-raw count reconciliation query
- solution and stakeholder summary
