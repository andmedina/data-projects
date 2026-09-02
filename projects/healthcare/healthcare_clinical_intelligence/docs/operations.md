# Operations Guide

This project is synthetic-only, but its control plane follows production-style conventions: durable run state, atomic data transactions, reconciled counts, persistent quality evidence, observable migration state, and consumer-contract verification.

## Run lifecycle

Every database ingestion creates an `operational.pipeline_run` row before processing begins. Raw/core writes occur in a separate transaction. Success and partial-success paths record completion time plus source, loaded, duplicate, and rejected counts. An exception rolls back partial writes and stores the exception type and bounded message in a terminal `failed` run.

For FHIR, claims, and HL7 source files, this invariant must hold:

```text
records_seen = records_loaded + records_duplicates + records_rejected
```

HL7 mapping rejects are recorded separately in `details.mapping_rejected`; they do not change the raw-source count equation.

## Health report

```bash
hci operations-report --dsn "$HCI_DATABASE_DSN"
```

Release-blocking current-state signals are:

- `stale > 0`: a run has remained `running` for more than two hours;
- `missing_completion > 0`: a terminal run lacks `completed_at`; or
- `count_mismatches > 0`: a populated run violates the count invariant.

`failed` is historical evidence, not automatically a current release failure. Investigate its timestamp and error details, confirm a later successful recovery, and retain the record.

## Quality gate

`hci quality-gate` executes every enabled definition, persists all individual results, and returns nonzero for an error-severity violation. Warnings remain visible but are non-blocking unless `--fail-on-warning` is selected. Three operability controls cover stale runs, missing terminal timestamps, and count reconciliation.

## Schema changes

`hci db-migrate` expands the controlled `\\ir` include graph, computes SHA-256 over the effective SQL, and records the checksum and execution time in `operational.schema_migration`. Reapplying an identical bundle returns `already_current`. A changed checksum reruns the idempotent SQL and increments `application_count`.

Never edit an already released destructive migration into `000_init.sql`. This portfolio currently uses backward-compatible `create if not exists`, `alter ... add column if not exists`, and replaceable-view changes. A future destructive production change should be a separately reviewed forward migration with recovery steps.

## Dashboard delivery

Every export must be followed by:

```bash
hci dashboard-validate output/dashboard
```

The validator independently recomputes file sizes, headers, row counts, and checksums and rejects unsafe paths. A valid bundle is still synthetic and must not be treated as a clinical product.

## Recommended production integrations

The repository deliberately stops short of choosing an alerting vendor. In a deployed environment, send nonzero stale/missing/count signals, quality failures, and CI failures to the accountable on-call route. Send no source payload or clinical identifier in alerts.
