# Local Integration Validation Evidence

The Docker-based Phase 1 workflow was executed locally against PostgreSQL and Airflow.

## PostgreSQL FHIR pipeline

The sample FHIR Bundle produced:

| Measure | Result |
| --- | ---: |
| Source resources | 4 |
| Raw resources loaded | 3 |
| Rejected/quarantined resources | 1 |
| Core patients | 1 |
| Core encounters | 1 |
| Core observations | 1 |
| Orphan observations | 0 |
| Invalid encounter periods | 0 |

The ED mart returned one January 2025 emergency encounter for one patient, with 1.00 encounters per patient.

## Idempotency and scale

Rerunning the same sample loaded zero new raw resources and identified three existing resource payloads as duplicates. A deterministic 100-patient synthetic Bundle contained 582 FHIR resources; all 582 loaded successfully. The resulting core model contained 101 patients, 242 encounters, and 242 observations, with zero orphan observations and zero invalid encounter periods. The ED mart contained 12 reporting months and 69 ED encounters.

## Airflow orchestration

The `clinical_fhir_pipeline` DAG was registered, unpaused, and triggered in the Docker Airflow standalone environment. The following tasks completed successfully:

1. `ingest_validate_and_quarantine_fhir`
2. `transform_and_load_core`
3. `publish_quality_report`

The manual DAG run completed with a `success` state. A scheduled run also completed successfully after the DAG was unpaused.

## HAPI FHIR REST integration

The local HAPI FHIR R4 server served its CapabilityStatement at `/fhir/metadata`. The project `fhir-publish` command upserted the four-resource sample Bundle through the REST API. The incremental client then retrieved and loaded one Patient, one Encounter, and two Observations; the malformed Observation was quarantined by the same validation rule used for file ingestion.

An incremental rerun used the saved Patient watermark, loaded zero new records, and identified the returned Patient as a duplicate. This validates source watermarking and idempotency against the live API.

## Multi-source resolution

The HAPI and Synthea copies of the same FHIR resource IDs initially exposed a staging upsert conflict. Staging now ranks resource versions by `last_updated_at`, ingestion timestamp, and raw identifier, retaining only the latest version per resource type and source resource ID. After applying that correction, the core load completed successfully with 101 patients, 242 encounters, 242 observations, zero orphan observations, and zero invalid encounter periods.

## Environment note

The local machine already used `localhost:5432` for another PostgreSQL service. This project therefore uses host port `55432`; container-to-container services continue to use PostgreSQL port `5432`.
