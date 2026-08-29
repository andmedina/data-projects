# Data Quality

Controls are implemented at ingestion, staging, core, and analytics boundaries.

| Control | Action on failure |
| --- | --- |
| Supported FHIR type and required IDs | quarantine with reason code |
| Required Patient reference on Encounter/Observation | quarantine |
| Stable payload hash/source ID | skip duplicate on rerun |
| Encounter end before start | reject from core load |
| Unresolved cross-resource reference | quarantine with patient/encounter reason code |
| Claims paid/allowed/billed hierarchy | quarantine claim line |

Validation SQL lives in `sql/validation/`; ticket evidence must state affected scope, root cause, correction, backfill, and prevention.
