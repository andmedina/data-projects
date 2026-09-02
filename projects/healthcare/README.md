# Healthcare Data Projects

This directory contains synthetic-only healthcare engineering projects. No repository fixture, output, log, screenshot, or dashboard may contain PHI.

| Project | Focus |
| --- | --- |
| [Healthcare Clinical Intelligence](healthcare_clinical_intelligence/) | FHIR, claims, HL7, Airflow, PostgreSQL clinical modeling, persistent quality gates, dashboard contracts, governed synthetic ML, population health, OMOP-compatible extracts, imaging metadata, and production-style CI/operations controls |
| [Healthcare Claims ETL](healthcare_claims_etl/) | Relational claims ingestion, transformation, validation, and analytics |

The clinical-intelligence platform is the broader interoperability and longitudinal analytics project. It includes a disposable PostgreSQL end-to-end smoke test, checksum-tracked migrations, contract verification, observability controls, and release documentation. The claims ETL project remains a focused claims-processing implementation.
