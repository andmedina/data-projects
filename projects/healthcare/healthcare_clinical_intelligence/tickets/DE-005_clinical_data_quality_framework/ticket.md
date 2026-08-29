# DE-005 — Clinical Data-Quality Framework

## Objective

Replace transient quality counts with an auditable framework that defines controls, stores every evaluation, supports thresholds and severity, and can stop an orchestrated pipeline when critical expectations fail.

## Acceptance criteria

- [x] Persist enabled checks, descriptions, dimensions, severities, and failure thresholds.
- [x] Persist immutable run-level results with observed values and evaluation timestamps.
- [x] Fail the command process when an error-severity threshold is exceeded.
- [x] Allow warning-severity exceptions by default and support strict warning enforcement.
- [x] Treat missing or unexecutable enabled checks as blocking configuration errors.
- [x] Integrate the gate as the final Airflow task.
- [x] Publish the latest persisted results through the dashboard contract.
- [x] Document configuration, operations, validation, and stakeholder interpretation.

## Default policy

Structural integrity, temporal validity, required reporting fields, and financial reconciliation are error-severity checks with zero tolerance. Quarantine counts are warning-severity checks because rejected records are intentionally retained and can be expected in controlled negative fixtures. Production thresholds require data-owner approval.

Status: complete for the synthetic platform scope.
