# DE-011 Solution

Implemented a two-job GitHub Actions workflow: static/unit quality and a PostgreSQL 16 service integration. The integration runner applies the expanded SQL bundle twice, loads controlled FHIR/claims/HL7 data, refreshes the canonical, mart, OMOP-compatible, imaging, and governance paths, validates the persistent gate and dashboard contract, captures query timings, then repeats every ingestion path to prove idempotency.

`operational.schema_migration` stores expanded-SQL SHA-256, timing, and application count. `operational.pipeline_run_health` derives stale, missing-completion, and count-mismatch flags from durable run metadata. Load exceptions roll back partial data and preserve a bounded error description in the failed run.

Dashboard contract `1.0.0` records CSV columns, rows, bytes, and SHA-256. The validator recomputes each value and rejects missing files, duplicate names, unsafe paths, and tampering. Performance checks verify required indexes and run five representative `EXPLAIN ANALYZE` plans under a deliberately broad smoke threshold.

Developer commands are normalized through `Makefile`, with Ruff, formatting, mypy, tests, coverage, and a pre-commit configuration. Operations, troubleshooting, performance, and release documentation define what the controls do and do not prove.
