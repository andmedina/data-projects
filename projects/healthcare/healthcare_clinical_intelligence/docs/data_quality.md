# Data Quality

Controls are implemented at ingestion, staging, core, and analytics boundaries. DE-005 adds a persistent gate so each evaluation is auditable and usable by orchestration and dashboards.

| Control | Action on failure |
| --- | --- |
| Supported FHIR type and required IDs | quarantine with reason code |
| Required Patient reference on Encounter/Observation | quarantine |
| Stable payload hash/source ID | skip duplicate on rerun |
| Encounter end before start | reject from core load |
| Unresolved cross-resource reference | quarantine with patient/encounter reason code |
| Claims paid/allowed/billed hierarchy | quarantine claim line |

## Persistent gate

`operational.quality_check_definition` holds each control's dimension, severity, tolerance, and enabled state. `operational.quality_run` and `operational.quality_result` retain execution history and evidence. Each result snapshots its evaluated dimension, severity, and threshold so later policy changes cannot reinterpret historical runs. Executable SQL remains reviewed application code in `quality.py`; database configuration cannot inject arbitrary SQL.

Default error-severity checks enforce:

- observation-to-patient integrity;
- encounter temporal validity;
- completed ED encounter reporting timestamps;
- claim-line referential integrity;
- exact claim header-to-line financial reconciliation;
- final laboratory result or documented absent-reason completeness; and
- final laboratory effective-time completeness.

FHIR, claim, and HL7 quarantine volumes are warning-severity checks. This keeps deliberately invalid test fixtures visible without failing a normal development pipeline. Use strict mode for a zero-warning release gate.

```bash
PYTHONPATH=src python -m healthcare_clinical_intelligence.cli quality-gate \
  --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"

PYTHONPATH=src python -m healthcare_clinical_intelligence.cli quality-gate \
  --fail-on-warning \
  --dsn "postgresql://healthcare_app:change-me@localhost:55432/healthcare_clinical_intelligence"
```

An error-severity violation, check execution error, missing executable check, or empty enabled-check catalog returns process exit code 1. Normal warning violations persist `passed_with_warnings` and return zero; strict mode makes them blocking.

Thresholds are explicit policy. For example, a data owner can tolerate up to two retained synthetic FHIR rejects while preserving history:

```sql
update operational.quality_check_definition
set failure_threshold = 2,
    updated_at = current_timestamp
where check_name = 'quarantined_fhir_records';
```

Project migrations preserve configured thresholds and enabled states. Validation SQL lives in `sql/validation/` and the DE-005 ticket; incident evidence must state affected scope, root cause, correction, backfill, and prevention.
