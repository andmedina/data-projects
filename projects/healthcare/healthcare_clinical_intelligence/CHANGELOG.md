# Changelog

All notable platform changes are recorded here. Dates use ISO 8601.

## 0.2.0 - 2026-09-02

### Added

- Monorepo-root GitHub Actions design for static quality and live PostgreSQL integration.
- Disposable-database smoke runner covering FHIR, claims, HL7, OMOP-compatible extracts, imaging metadata, model governance, quality, dashboard delivery, performance, and idempotent reruns.
- Checksum-tracked schema application and runtime operations reporting.
- Durable pipeline counts and failure details plus stale, completion, and reconciliation controls.
- Dashboard contract version `1.0.0` with column, size, and SHA-256 verification.
- Required-index and representative-query performance guardrails.
- Make targets, Ruff, mypy, coverage, pre-commit, operations guidance, troubleshooting, and release documentation.

### Changed

- Database ingestion now persists a run marker before processing and rolls back partial data on exceptions.
- Dashboard pipeline-run exports include source, loaded, duplicate, and rejected counts.

## 0.1.0 - 2026-09-01

- Initial synthetic healthcare intelligence platform through FHIR, claims, HL7, Airflow, quality, dashboard exports, ML governance, population health, OMOP-compatible extracts, and imaging metadata.
