# Troubleshooting

## PostgreSQL is unreachable

Confirm Docker and the mapped port:

```bash
docker compose ps
docker compose logs postgres
```

The host default is port `55432`; GitHub Actions uses its isolated port `5432`. If `55432` is occupied, set a different `POSTGRES_PORT` in `.env` and update the DSN.

## Migration fails

Run `hci db-migrate` directly and retain the full PostgreSQL error. The migration is transactional: a failed SQL bundle is rolled back, while the schema-migration ledger created before it remains available. Do not manually mark a checksum as applied.

For a reproducible diagnosis that leaves the development database untouched, run `make integration`. It provisions and removes its own `hci_smoke_<random>` database.

## A pipeline is stale

Use `hci operations-report` and query `operational.pipeline_run_health` for `is_stale = true`. Verify no worker is still processing the run. Retain the stale row as evidence; do not rewrite it as successful. A production recovery procedure should mark an abandoned run failed with an incident reference, then replay the immutable raw input under a new run ID.

The local loaders automatically persist failures raised during ingestion. A machine interruption can still leave `running` state, which is why stale detection exists.

## Quality gate returns warnings

Warnings are intentional review items. The checked-in synthetic fixtures currently produce two expected categories in the complete smoke path: a deliberate quarantined FHIR record and unresolved OMOP terminology mappings pending a governed Athena vocabulary. New warning categories or larger counts require investigation.

## Dashboard validation fails

Regenerate the entire bundle from PostgreSQL. Do not edit CSVs or `manifest.json` independently. Header, row-count, byte-count, and checksum errors usually mean a partial copy or manual edit. Unsafe-path errors indicate an invalid manifest and must never be bypassed.

## Performance smoke test fails

Run `hci performance-report` and inspect `missing_indexes` and `slow_queries`. Apply the latest migration first. The five-second threshold is a regression guardrail on synthetic data, not a capacity promise. Compare query plans and dataset size before changing the threshold.

## Temporary smoke database remains after interruption

The test normally drops its database in a `finally` block. If the process or Docker daemon was forcibly terminated, list databases with names beginning `hci_smoke_`, verify no sessions or useful data exist, and remove only the exact generated database. Never use a wildcard deletion command.
