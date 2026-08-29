# Healthcare Clinical Intelligence Platform

An end-to-end, synthetic healthcare data platform that demonstrates FHIR ingestion, layered clinical data modeling, data-quality controls, reconciliation, and healthcare analytics.

All data in this repository will be synthetic. It must never contain PHI.

## Phase 1 scope

Phase 1 establishes a reproducible clinical/FHIR foundation:

- Synthea-generated FHIR R4 data as the baseline source;
- `Patient`, `Encounter`, and `Observation` ingestion;
- raw, staging, core, and analytics layers in PostgreSQL;
- rejected-record quarantine and source-to-target reconciliation;
- data-quality checks; and
- one initial emergency-department utilization mart.

The HAPI FHIR API is an optional integration path. Claims, HL7 v2, orchestration, dashboards, ML, OMOP, and imaging are deliberately deferred until the foundation is proven.

## Architecture

```text
Synthea FHIR R4 export / HAPI FHIR API
              |
              v
       raw source records
              |
              v
  staging + validation + quarantine
              |
              v
       canonical clinical model
              |
              v
 utilization analytics mart + reports
```

See [the architecture](docs/architecture.md), [project charter](docs/project_charter.md), and [roadmap](docs/roadmap.md).

## Repository layout

- `src/` — application code for ingestion, validation, and transformations
- `sql/` — database DDL, transformations, validations, and analysis queries
- `data/samples/` — small, non-PHI test fixtures only
- `docs/` — architecture, definitions, mappings, and operating guidance
- `tickets/` — realistic healthcare data work items and their evidence
- `tests/` — automated tests

## Current status

The local FHIR runner, FHIR validation/quarantine flow, controlled HL7 parser, claims validation rules, PostgreSQL schemas, data-quality queries, and ED-utilization mart are implemented as a reproducible foundation. The first implementation ticket is [DE-001](tickets/DE-001_fhir_patient_encounter_ingestion/ticket.md). See the [runbook](docs/runbook.md) to run it.

Later-domain contracts are included for claims, HL7, Airflow, readmission ML, OMOP, dashboards, and imaging. They are planned extensions—not claims of finished production integrations.

## Guiding rules

1. Preserve source payloads in the raw layer so every load can be replayed.
2. Make reruns idempotent and record failures explicitly.
3. Document the grain, assumptions, lineage, and validation for each analytical output.
4. Validate clinical metrics independently before presenting them.
5. Never represent synthetic-data analysis or models as clinically validated.
