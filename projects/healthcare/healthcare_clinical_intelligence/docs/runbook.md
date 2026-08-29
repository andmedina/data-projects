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
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-postgres data/samples/fhir_bundle.json --dsn "postgresql://healthcare_app:change-me@localhost:5432/healthcare_clinical_intelligence"
```

Then run `sql/core/021_load_core.sql` and `sql/validation/041_reconciliation.sql`. Do not place Synthea exports under version control.

Or run the complete Phase 1 FHIR path with one command after the database is initialized:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-pipeline data/samples/fhir_bundle.json --dsn "postgresql://healthcare_app:change-me@localhost:5432/healthcare_clinical_intelligence"
```

It returns ingestion counts and core-model quality results. A healthy sample run has 1 patient, 1 encounter, 1 observation, zero orphan observations, and one quarantined record.

## Other source demonstrations

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli hl7-file data/samples/adt_a01.hl7 --output output/hl7
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli claims-file data/samples/claims.csv --output output/claims
```

These validate and quarantine controlled synthetic inputs. Their database mappings are next-phase extensions; they do not replace a certified HL7/X12 implementation.

## Generate larger synthetic fixtures

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli generate-synthetic --patients 250 --seed 42 --output data/synthetic/fhir_bundle.json
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-file data/synthetic/fhir_bundle.json --output output/generated
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli ed-utilization output/generated/accepted.jsonl
```

The generator makes deterministic, clearly synthetic fixtures for development only; Synthea remains the preferred realistic source for portfolio demonstrations.

For an API-backed incremental load after the optional HAPI profile is populated:

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli fhir-incremental Patient --base-url http://localhost:8080/fhir --dsn "postgresql://healthcare_app:change-me@localhost:5432/healthcare_clinical_intelligence"
```

The checkpoint advances only after the full paginated request completes successfully.

## Optional services

```bash
docker compose --profile fhir-api up hapi-fhir
docker compose --profile orchestration up airflow
```

The Airflow profile builds the project image, waits for the PostgreSQL health check, and runs the `clinical_fhir_pipeline` DAG with real ingestion, core-load, and quality-report CLI tasks. Open Airflow at `http://localhost:8081`, unpause the DAG, and trigger it manually.
