# Architecture

## Layered data flow

| Layer | Purpose | Phase 1 examples |
| --- | --- | --- |
| Source | Original synthetic clinical source | Synthea FHIR R4 export; optional HAPI API |
| Raw | Immutable source fidelity and replay | resource JSON, resource type, source ID, load metadata |
| Staging | Parsed, typed, normalized records | `stg_patient`, `stg_encounter`, `stg_observation` |
| Core | Canonical clinical relationships | patient, encounter, observation entities |
| Analytics | Purpose-built, documented queries | ED utilization mart |

## Reliability controls

- Raw records retain the original JSON payload and a source identifier.
- Each run has a run ID, timestamps, counts, and outcome status.
- Validation failures are written to a quarantine table with a reason code; they are never silently dropped.
- Natural source IDs and payload hashes enable idempotent loads.
- Reconciliation compares source, raw, valid staging, quarantined, core, and mart counts with documented exclusions.

## FHIR mapping principles

FHIR references are parsed as references, not assumed foreign keys. The source resource ID, reference string, extracted referenced ID, coding system, coding code, and coding display are retained when applicable. Optional FHIR elements are handled explicitly.

## Security and privacy

The repository accepts synthetic data only. Credentials are environment variables, not source-controlled files. Documentation and examples must avoid real identifiers, screenshots, exports, or sample records derived from real care.
