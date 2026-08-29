# Data Dictionary — Phase 1

| Entity | Grain | Primary identifier |
| --- | --- | --- |
| `raw.fhir_resource` | one ingested source payload version | `raw_resource_id` |
| `operational.quality_check_definition` | one named quality-control policy | `check_name` |
| `operational.quality_run` | one quality-gate execution | `quality_run_id` |
| `operational.quality_result` | one check result per quality run | `quality_run_id` + `check_name` |
| `core.patient` | one source patient | `patient_id` |
| `core.encounter` | one source encounter | `encounter_id` |
| `core.observation` | one source observation | `observation_id` |
| `core.condition_occurrence` | one patient condition | `condition_id` |
| `core.procedure_occurrence` | one patient procedure | `procedure_id` |
| `core.medication_request` | one medication request | `medication_request_id` |
| `core.coverage` | one patient coverage record | `coverage_id` |
| `core.organization` | one source organization | `organization_id` |
| `core.provider` | one source practitioner | `provider_id` |
| `core.claim` | one claim header | `claim_id` |
| `core.claim_line` | one claim service line | `claim_line_id` |
| `core.hl7_observation` | one OBX result per HL7 message | `hl7_observation_id` |
| `mart.ed_utilization_monthly` | reporting month | `reporting_month` |
| `mart.clinical_activity_monthly` | reporting month | `reporting_month` |
| `mart.claim_cost_monthly` | reporting month | `reporting_month` |
