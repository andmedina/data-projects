-- PostgreSQL image entrypoints execute files only at this directory level.
-- Keep the authoritative DDL in the layer folders; this file includes it in order.
\ir raw/001_raw_schema.sql
\ir raw/002_hl7_claims_imaging_schema.sql
\ir raw/003_incremental_checkpoints.sql
\ir raw/004_claims_quarantine.sql
\ir raw/005_hl7_quarantine.sql
\ir staging/010_staging_views.sql
\ir core/020_core_schema.sql
\ir marts/030_ed_utilization.sql
\ir marts/031_claims_cost.sql
\ir marts/032_clinical_activity.sql
