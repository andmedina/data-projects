# Data Dictionary — Phase 1

| Entity | Grain | Primary identifier |
| --- | --- | --- |
| `raw.fhir_resource` | one ingested source payload version | `raw_resource_id` |
| `core.patient` | one source patient | `patient_id` |
| `core.encounter` | one source encounter | `encounter_id` |
| `core.observation` | one source observation | `observation_id` |
| `core.condition_occurrence` | one patient condition | `condition_id` |
| `core.procedure_occurrence` | one patient procedure | `procedure_id` |
| `core.medication_request` | one medication request | `medication_request_id` |
| `core.coverage` | one patient coverage record | `coverage_id` |
| `core.organization` | one source organization | `organization_id` |
| `core.provider` | one source practitioner | `provider_id` |
| `mart.ed_utilization_monthly` | reporting month | `reporting_month` |
