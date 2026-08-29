# Project Charter

## Purpose

Build a portfolio-grade, synthetic healthcare data platform that reflects how a healthcare data team ingests, validates, models, reconciles, and analyzes clinical data.

## Users and outcomes

The platform is designed to demonstrate skills relevant to healthcare data engineering, analytics, and data science. Its first business outcome is a trustworthy ED-utilization dataset, not a dashboard-first prototype.

## In scope for Phase 1

- FHIR R4 `Patient`, `Encounter`, and `Observation` resources
- Synthea data generation/export and optional HAPI FHIR API retrieval
- PostgreSQL raw, staging, core, and analytics layers
- FHIR reference parsing, validation, quarantine, idempotency, and reconciliation
- ED-utilization mart plus a documented metric definition

## Explicitly out of scope for Phase 1

- real patient data or PHI
- claims/X12, HL7 v2, Airflow, Power BI deliverables, ML, OMOP, and DICOM
- clinical decision support or clinical validation

## Success criteria

Another engineer can clone the repository, load synthetic FHIR data, run the pipeline, inspect rejected records and reconciliation results, and reproduce the documented utilization metric without hidden manual steps.

## Decisions

Synthea FHIR exports are the required reproducible input. HAPI FHIR remains an optional service integration so infrastructure does not obscure the data-engineering work. PostgreSQL is the system of record; dbt and Airflow will be introduced only when their operational value is demonstrated.
