# Lineage

`FHIR Observation` → `raw.fhir_resource` → `staging.stg_observation` → `core.observation` → future laboratory/utilization marts.

`FHIR Encounter` → `raw.fhir_resource` → `staging.stg_encounter` → `core.encounter` → `mart.ed_utilization_monthly` → Power BI utilization page.

Every raw row retains source system, resource type, source ID, payload hash, and pipeline run ID. These fields support replay and reconciliation.
