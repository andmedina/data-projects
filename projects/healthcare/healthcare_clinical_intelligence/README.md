# Healthcare Clinical Intelligence Platform

An end-to-end, synthetic healthcare data platform that demonstrates FHIR ingestion, layered clinical data modeling, data-quality controls, reconciliation, and healthcare analytics.

All data in this repository will be synthetic. It must never contain PHI.

## Phase 1 scope

Phase 1 establishes a reproducible clinical/FHIR foundation:

- Synthea-generated FHIR R4 data as the baseline source;
- `Patient`, `Encounter`, `Observation`, `Condition`, `Procedure`, `MedicationRequest`, `Practitioner`, `Organization`, and `Coverage` ingestion;
- raw, staging, core, and analytics layers in PostgreSQL;
- rejected-record quarantine and source-to-target reconciliation;
- persistent threshold-based data-quality gates;
- ED intensity, eligibility-aware ED utilization, clinical-activity, and claims-cost marts with a dashboard export contract; and
- typed laboratory values, a lab-result completeness mart, and a reproduced missing-result incident.

The HAPI FHIR API, live PostgreSQL workflow, and Airflow execution are optional integration paths. The repository already includes controlled HL7 ADT/ORM/ORU persistence, claims adjudication modeling, dashboard-ready exports, and a temporally correct readmission-cohort export. OMOP and imaging remain later extensions.

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

Implemented locally:

- FHIR Bundle ingestion with validation, idempotency metadata, quarantine, reference-resolution controls, and core-load SQL;
- controlled HL7 v2 ADT lifecycle, ORM order, and ORU result persistence plus claims CSV validation, raw loading, quarantine, payer/provider dimensions, diagnosis/procedure coding, adjustment lineage, and claim/claim-line modeling;
- auditable quality definitions, run history, result evidence, and an Airflow-blocking critical gate;
- typed FHIR Observation values/UCUM units plus missing-laboratory-result detection and recovery evidence;
- incremental FHIR API client and PostgreSQL checkpoint design;
- deterministic synthetic FHIR generation, database-backed dashboard bundle, and temporal readmission cohort export;
- typed Coverage periods, distinct payer member-month denominators, and ED encounters per 1,000 eligible member months;
- governed logistic-regression readmission baseline with strict patient/time separation, calibration, subgroup review, experiment registry, model card, and technical approval gate; and
- PostgreSQL/Airflow/HAPI configuration and CI test coverage.

The Docker PostgreSQL, Airflow, and HAPI FHIR API workflows have been validated locally; see [validation evidence](docs/validation_evidence.md). OMOP and imaging remain later extensions. See the [runbook](docs/runbook.md) for runnable commands.

## Portfolio relationship

This project complements the sibling [Healthcare Claims ETL Pipeline](../healthcare_claims_etl/): that project focuses on relational claims ETL, while this platform focuses on clinical interoperability, source fidelity, reconciliation, and longitudinal analytics.

## Guiding rules

1. Preserve source payloads in the raw layer so every load can be replayed.
2. Make reruns idempotent and record failures explicitly.
3. Document the grain, assumptions, lineage, and validation for each analytical output.
4. Validate clinical metrics independently before presenting them.
5. Never represent synthetic-data analysis or models as clinically validated.
