# Project Charter

## Purpose

Build a portfolio-grade, synthetic healthcare data platform that reflects how a healthcare data team ingests, validates, models, reconciles, and analyzes clinical data.

## Users and outcomes

The platform is designed to demonstrate skills relevant to healthcare data engineering, analytics, and data science. Its initial ED-activity outcome now anchors a broader set of independently validated healthcare data products.

## Current implemented scope

- FHIR R4 clinical resources with typed Observation/laboratory values
- Synthea data generation/export and optional HAPI FHIR API retrieval
- PostgreSQL raw, staging, core, and analytics layers
- FHIR reference parsing, validation, quarantine, idempotency, and reconciliation
- ED, clinical-activity, claims-cost, and lab-completeness analytics
- controlled claims and HL7 paths, persistent quality gates, Airflow, dashboard exports, and a temporal ML baseline

## Explicitly out of scope

- real patient data or PHI
- production X12/HL7 certification, production Power BI deployment, full OMOP, and DICOM pixel data
- clinical decision support, clinical interpretation, or clinical validation

## Success criteria

Another engineer can clone the repository, load synthetic FHIR data, run the pipeline, inspect rejected records and reconciliation results, and reproduce the documented utilization metric without hidden manual steps.

## Decisions

Synthea or deterministic synthetic FHIR exports are the required reproducible input. HAPI FHIR remains an optional service integration. PostgreSQL is the analytical system of record, and Airflow enforces the persisted critical quality gate.
