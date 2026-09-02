# Lineage

`FHIR Observation` → `raw.fhir_resource` → `staging.stg_observation` → typed `core.observation` → `mart.lab_result_completeness_monthly` → dashboard lab/data-trust page.

`FHIR Encounter` → `raw.fhir_resource` → `staging.stg_encounter` → `core.encounter` → `mart.ed_utilization_monthly` → Power BI utilization page.

`FHIR Coverage` + eligible `FHIR Encounter` → raw/staging/core clinical layers → distinct patient/payer/month expansion → `mart.member_eligibility_monthly` + `mart.ed_utilization_eligible_monthly` → Power BI population-health page.

`FHIR Condition / Procedure / MedicationRequest` → `raw.fhir_resource` → typed staging views → canonical core entities → `mart.clinical_activity_monthly` → Power BI clinical-activity page.

`Claims CSV line` → versioned `raw.claim_line` → latest `staging.stg_claim_line` → payer/provider dimensions + claim/header detail + diagnosis/procedure/adjustment children → `mart.claim_cost_monthly` → Power BI claims-cost page.

`HL7 ADT / ORM / ORU message` → exact `raw.hl7_message` text → encounter/order/observation events in core → current-state HL7 marts → dashboard HL7-operations datasets.

`operational.pipeline_run` + core quality checks + analytics marts → `dashboard-export` → versioned file contract and refresh manifest.

Synthetic FHIR encounters → accepted canonical file records → readmission cohort → strict patient/time split → holdout predictions + governed model report + registry/model card → dashboard model-governance datasets.

canonical core/claim/quarantine tables → named checks in `quality.py` → `operational.quality_run` + `operational.quality_result` → Airflow gate + dashboard data-trust page.

canonical patient/coverage/clinical events → `omop.entity_id_map` → eight OMOP v5.4-compatible views → domain reconciliation + vocabulary-status datasets → dashboard interoperability page.

FHIR ImagingStudy JSON metadata → latest staging study/series views → `core.imaging_study` + `core.imaging_series` → count controls → monthly imaging activity dashboard dataset. Pixel data never enters this lineage.

Every raw row retains source system, resource type, source ID, payload hash, and pipeline run ID. These fields support replay and reconciliation.
