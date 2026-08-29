# DE-005 Solution — Persistent Quality Gates

## Design

The framework separates policy, execution, and evidence:

- `operational.quality_check_definition` stores the enabled control catalog, business description, quality dimension, severity, and tolerated failure count.
- `healthcare_clinical_intelligence.quality` owns reviewed executable SQL for each named definition. This prevents arbitrary database configuration from becoming executable application SQL.
- `operational.quality_run` records the trigger, linked pipeline run when supplied, policy mode, timestamps, and overall gate status.
- `operational.quality_result` stores the observed value, evaluated dimension/severity/threshold snapshot, status, and diagnostic details for every check. Later policy changes therefore cannot reinterpret historical evidence.

Critical violations and execution/configuration errors fail the CLI process. Warning threshold violations produce `passed_with_warnings` in normal mode. `--fail-on-warning` promotes warnings to blocking gate results without rewriting their underlying severity, preserving accurate audit semantics.

## Failure behavior

Each executable check runs inside a database savepoint. A check-query error is rolled back to that savepoint and persisted as an `error` result; other checks can still complete, and the overall gate fails. An empty enabled-check set also fails closed.

The Airflow DAG now ends with `enforce_quality_gate`. BashOperator propagates the CLI's nonzero exit code, preventing a structurally invalid core load from appearing successful.

## Local validation

The live synthetic PostgreSQL environment evaluated eight enabled controls. Seven passed. The two deliberately invalid FHIR fixtures already retained in quarantine exceeded the default warning threshold, so normal mode completed as `passed_with_warnings`. Strict mode evaluated the same evidence and returned exit code 1 as designed.

No error-severity check exceeded its threshold: encounter time validity, ED reporting completeness, patient/observation integrity, claim referential integrity, and claim header/line reconciliation all passed.

The finalized Airflow DAG then completed both manual run `de005_policy_snapshot_validation` and its scheduled run successfully. For the manual run, `ingest_validate_and_quarantine_fhir`, `transform_and_load_core`, and `enforce_quality_gate` all reached `success`. The persisted Airflow-triggered quality result became the latest dashboard data-trust snapshot.
