# DE-011: Production-style platform reliability gate

## Context

The platform's domain pipelines were validated locally, but the nested GitHub workflow exercised only unit tests and was not discoverable by GitHub Actions at the monorepo root. Schema application had no checksum ledger, consumer exports had row counts without integrity hashes, and operational runs did not persist reconciled counts or terminal exception details.

## Acceptance criteria

1. A monorepo-root workflow runs static quality and a clean PostgreSQL integration job.
2. Schema application is idempotent and retains checksum/timing evidence.
3. FHIR, claims, and HL7 runs persist source, loaded, duplicate, and rejected counts; exceptions retain a terminal failed run.
4. Stale, missing-completion, and count-mismatch controls block the quality gate.
5. Dashboard delivery has a versioned, independently verifiable contract.
6. Representative queries and required indexes have automated smoke guardrails.
7. One disposable-database command runs all controlled domains twice without changing the shared development database.

## Constraints

- Synthetic data only.
- No claim of production capacity or clinical validation.
- No destructive migration against an existing database.
- Temporary database cleanup must resolve one exact generated name, never a wildcard.
