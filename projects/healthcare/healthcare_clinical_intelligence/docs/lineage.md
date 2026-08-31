# Lineage

`FHIR Observation` → `raw.fhir_resource` → `staging.stg_observation` → typed `core.observation` → `mart.lab_result_completeness_monthly` → dashboard lab/data-trust page.

`FHIR Encounter` → `raw.fhir_resource` → `staging.stg_encounter` → `core.encounter` → `mart.ed_utilization_monthly` → Power BI utilization page.

`FHIR Condition / Procedure / MedicationRequest` → `raw.fhir_resource` → typed staging views → canonical core entities → `mart.clinical_activity_monthly` → Power BI clinical-activity page.

`Claims CSV line` → versioned `raw.claim_line` → latest `staging.stg_claim_line` → payer/provider dimensions + claim/header detail + diagnosis/procedure/adjustment children → `mart.claim_cost_monthly` → Power BI claims-cost page.

`operational.pipeline_run` + core quality checks + analytics marts → `dashboard-export` → versioned file contract and refresh manifest.

canonical core/claim/quarantine tables → named checks in `quality.py` → `operational.quality_run` + `operational.quality_result` → Airflow gate + dashboard data-trust page.

Every raw row retains source system, resource type, source ID, payload hash, and pipeline run ID. These fields support replay and reconciliation.
