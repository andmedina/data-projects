# Runbook

## Local validation

Run the dependency-free synthetic FHIR demonstration:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-file data/samples/fhir_bundle.json --output output/demo
PYTHONPATH=src python -m pytest -q
```

The report must show 4 source records, 3 accepted records, and 1 quarantined Observation. Output is ignored by Git.

## Full developer verification

Install every development extra and run the static/unit gate:

```bash
make install-dev
make quality
```

With Docker PostgreSQL healthy, run the entire database path in a disposable database:

```bash
docker compose up -d postgres
make integration
```

The smoke test creates a database named `hci_smoke_<random>`, applies the expanded migration twice, loads FHIR, claims, ADT/ORM/ORU, OMOP-compatible views, imaging metadata, and model governance, then repeats the ingestion paths to prove idempotency. It validates the quality gate, dashboard checksums, required indexes, query timings, and operational run counts before dropping only that temporary database.

## PostgreSQL

```bash
cp .env.example .env
docker compose up postgres
```

The mounted SQL directory initializes raw, staging, core, mart, quarantine, and operational objects. For the database loader, install the optional driver and load a synthetic Bundle:

```bash
python -m pip install -e '.[postgres]'
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-postgres data/samples/fhir_bundle.json --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

Then run `sql/core/021_load_core.sql` and `sql/validation/041_reconciliation.sql`. Do not place Synthea exports under version control.

Or run the complete Phase 1 FHIR path with one command after the database is initialized:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-pipeline data/samples/fhir_bundle.json --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

It returns ingestion counts and core-model quality results. A healthy sample run has 1 patient, 1 encounter, 1 observation, zero orphan observations, and one quarantined record.

## Other source demonstrations

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli hl7-file data/samples/adt_a01.hl7 --output output/hl7
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli claims-file data/samples/claims.csv --output output/claims
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli claims-file data/samples/claims_expanded.csv --output output/claims-expanded
```

These validate and quarantine controlled synthetic inputs; claims and each supported HL7 profile also have canonical PostgreSQL paths. They do not replace certified HL7/X12 implementations.

Load each controlled HL7 profile after patient `p-001` exists in core:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli hl7-postgres data/samples/adt_lifecycle.hl7 --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli hl7-postgres data/samples/orm_o01.hl7 --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli hl7-postgres data/samples/oru_r01.hl7 --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

The lifecycle load should add three encounter events, the ORM load one order event, and the ORU load one observation when starting from an empty HL7 store. Identical reruns must report only raw duplicates and zero newly mapped canonical events. Run the quality gate and `tickets/DE-008_hl7_lifecycle_orders/validation.sql` before using the current-state marts.

After the FHIR sample has created patient `p-001`, run the expanded claims database path and its quality gate:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli claims-pipeline data/samples/claims_expanded.csv --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli quality-gate --triggered-by claims-expansion-validation --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

A second identical pipeline run must report three duplicates and zero newly loaded lines. The critical claims controls must all pass.

## Generate larger synthetic fixtures

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli generate-synthetic --patients 250 --seed 42 --output data/synthetic/fhir_bundle.json
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-file data/synthetic/fhir_bundle.json --output output/generated
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli ed-utilization output/generated/accepted.jsonl
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli eligible-ed-utilization output/generated/accepted.jsonl
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli readmission-cohort output/generated/accepted.jsonl
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli train-readmission-baseline output/readmission_cohort.csv --fail-on-governance
```

The generator makes deterministic, clearly synthetic fixtures for development only; Synthea remains the preferred realistic source for portfolio demonstrations. Training writes the report, holdout predictions, model card, and idempotent experiment registry beside the requested output. A governance failure returns exit code 1 when `--fail-on-governance` is present; passing still never grants clinical approval.

For an API-backed incremental load after the optional HAPI profile is populated:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-publish data/samples/fhir_bundle.json --base-url http://localhost:8080/fhir
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-incremental Patient --base-url http://localhost:8080/fhir --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

The checkpoint advances only after the full paginated request completes successfully.

## Dashboard export

Apply the latest SQL and export the complete dashboard contract from PostgreSQL:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli db-migrate --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli dashboard-export --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence" --output output/dashboard
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli dashboard-validate output/dashboard
```

Pass `--model-report output/readmission_baseline_report.json` to add model governance, calibration, subgroup, and approval-check datasets plus the governed model artifacts to the bundle.

## OMOP-compatible subset

Apply the latest migration, then refresh stable identifiers after any direct canonical-data change:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli db-migrate --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli omop-refresh --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
psql "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence" -f tickets/DE-009_omop_compatible_subset/validation.sql
```

`fhir-pipeline` and `core-load` refresh OMOP IDs automatically. The reconciliation output must show equal source and extract counts for all eight domains. Review `omop.source_to_standard_concept_status`; concept ID `0` means unresolved mapping. These views are not an OMOP-conformant CDM and must not be used as one.

The deterministic generator also emits one metadata-only ImagingStudy for every fourth patient. After loading it, run the gate and `tickets/DE-010_imaging_metadata/validation.sql`; declared series and instance counts and modality completeness must have zero violations. No pixel files are created.

Run the persistent quality gate before exporting:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli quality-gate --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

Then confirm that `data_quality.csv` contains no `fail` or `error` statuses. Run both `tickets/DA-001_ed_utilization/validation.sql` and `tickets/DA-002_eligibility_aware_ed_utilization/validation.sql` independently before publishing ED visuals. Warning rows require documented review. The generated output is intentionally ignored by Git.

Inspect runtime health and representative query timings at any point:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli operations-report --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli performance-report --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

Release candidates require zero stale runs, missing terminal timestamps, count mismatches, missing required indexes, or benchmark queries above the five-second smoke threshold. Historical failed runs remain visible and do not alone block a release; investigate and document any new failure.

For the controlled population-health validation, generate and load a Coverage-enabled synthetic Bundle, then verify the critical Coverage controls and independent mart reconciliation:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli generate-synthetic --patients 100 --seed 42 --output output/population_health/fhir_bundle_100.json
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-pipeline output/population_health/fhir_bundle_100.json --source-system synthetic_population_health_v1 --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli quality-gate --triggered-by population-health-validation --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
psql "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence" -f tickets/DA-002_eligibility_aware_ed_utilization/validation.sql
```

## Reproduce the missing-laboratory-result incident

Run this only with synthetic local data. The first gate is expected to return exit code 1:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-pipeline data/samples/fhir_lab_incident_missing.json --source-system lab_incident --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli quality-gate --triggered-by de006_missing_result --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

Load the later corrected source version and confirm recovery:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-pipeline data/samples/fhir_lab_incident_corrected.json --source-system lab_incident --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli quality-gate --triggered-by de006_corrected_result --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
psql "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence" -f tickets/DE-006_missing_laboratory_results/validation.sql
```

The corrected load should add one Observation payload version and identify the unchanged Patient and Encounter as duplicates. The validation must show two retained raw Observation versions, canonical hemoglobin `13.4 g/dL`, zero unexplained missing lab results, and 100% February 2025 completeness.

## Optional services

```bash
docker compose --profile fhir-api up hapi-fhir
docker compose --profile orchestration up airflow
```

The Airflow profile builds the project image, waits for the PostgreSQL health check, and runs the `clinical_fhir_pipeline` DAG with real ingestion, core-load, and persistent quality-gate CLI tasks. Open Airflow at `http://localhost:8081`, unpause the DAG, and trigger it manually. Error-severity threshold violations fail `enforce_quality_gate` and therefore fail the DAG run.

The first time Airflow discovers the DAG it is paused. Run `docker compose --profile orchestration exec -T airflow airflow dags unpause clinical_fhir_pipeline` before triggering it, or unpause it in the Airflow UI.
