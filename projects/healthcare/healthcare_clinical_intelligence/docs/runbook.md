# Runbook

## Local validation

Run the dependency-free synthetic FHIR demonstration:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-file data/samples/fhir_bundle.json --output output/demo
PYTHONPATH=src python -m pytest -q
```

The report must show 4 source records, 3 accepted records, and 1 quarantined Observation. Output is ignored by Git.

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
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli hl7-postgres data/samples/oru_r01.hl7 --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

These validate and quarantine controlled synthetic inputs; claims and ORU results also have canonical PostgreSQL paths. They do not replace certified HL7/X12 implementations.

## Generate larger synthetic fixtures

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli generate-synthetic --patients 250 --seed 42 --output data/synthetic/fhir_bundle.json
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-file data/synthetic/fhir_bundle.json --output output/generated
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli ed-utilization output/generated/accepted.jsonl
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli readmission-cohort output/generated/accepted.jsonl
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli train-readmission-baseline output/readmission_cohort.csv
```

The generator makes deterministic, clearly synthetic fixtures for development only; Synthea remains the preferred realistic source for portfolio demonstrations.

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
```

Run the persistent quality gate before exporting:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli quality-gate --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

Then confirm that `data_quality.csv` contains no `fail` or `error` statuses and run `tickets/DA-001_ed_utilization/validation.sql` independently before publishing ED visuals. Warning rows require documented review. The generated output is intentionally ignored by Git.

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
