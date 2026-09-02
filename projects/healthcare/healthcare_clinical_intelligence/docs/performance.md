# Performance Guardrails

The performance smoke test protects representative access paths from obvious regressions. It is not a load test, concurrency benchmark, service-level objective, or clinical capacity claim.

## Covered queries

`hci performance-report` runs PostgreSQL `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` for:

- executive core entity counts;
- monthly ED utilization;
- monthly claims cost;
- OMOP-compatible domain reconciliation; and
- monthly imaging activity.

Each representative query must complete within 5,000 milliseconds in the smoke environment. The JSON report retains planning and execution times separately.

## Required access paths

The migration creates and the smoke test verifies indexes for operational status/history, raw run lineage, patient/date clinical lookups, and active Coverage periods. An index-presence check is deterministic even when PostgreSQL reasonably chooses a sequential scan for the small synthetic dataset.

## Scaling beyond smoke tests

Before production use, establish environment-specific volume, concurrency, latency percentiles, resource saturation, connection-pool behavior, and recovery objectives using de-identified or synthetic data at expected scale. Do not extrapolate from this portfolio smoke test.
