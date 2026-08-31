# Architecture

## Layered data flow

| Layer | Purpose | Phase 1 examples |
| --- | --- | --- |
| Source | Original synthetic healthcare source | generated/Synthea FHIR R4, HAPI FHIR API, controlled claims CSV, HL7 v2 |
| Raw | Immutable source fidelity and replay | FHIR JSON, claim-line payloads, HL7 message text, source and run metadata |
| Staging | Parsed, typed, normalized records | patient, encounter, observation, condition, procedure, medication, coverage, latest claims-line views |
| Core | Canonical healthcare relationships | clinical entities, claim header/detail and dimensions, HL7 observations |
| Analytics | Purpose-built, documented queries | ED activity, clinical activity, claims-cost, and lab-completeness marts |
| Delivery | Reproducible consumer contracts | dashboard CSV bundle, manifest, validation evidence, model report |

## Reliability controls

- Raw records retain the original JSON payload and a source identifier.
- Each run has a run ID, timestamps, counts, and outcome status.
- Validation failures are written to a quarantine table with a reason code; they are never silently dropped.
- Natural source IDs and payload hashes enable idempotent loads.
- Staging selects the most recently updated payload for each resource type and source resource ID when multiple source systems provide the same record.
- Claims staging likewise selects the latest raw version per source-system/line identifier; original and adjustment claim lineage remains queryable in core while analytics select only the current adjudication state.
- Reconciliation compares source, raw, valid staging, quarantined, core, and mart counts with documented exclusions.
- Dashboard extracts are rebuilt from PostgreSQL and accompanied by a timestamped row-count manifest.
- Quality definitions, thresholds, gate runs, and individual results persist in the operational schema; critical failures propagate a nonzero process exit to Airflow.

## FHIR mapping principles

FHIR references are parsed as references, not assumed foreign keys. The source resource ID, reference string, extracted referenced ID, coding system, coding code, and coding display are retained when applicable. Optional FHIR elements are handled explicitly.

## Security and privacy

The repository accepts synthetic data only. Credentials are environment variables, not source-controlled files. Documentation and examples must avoid real identifiers, screenshots, exports, or sample records derived from real care.
