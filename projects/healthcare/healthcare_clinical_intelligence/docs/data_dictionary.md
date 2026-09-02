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
| `core.imaging_study` | one FHIR ImagingStudy metadata header | `imaging_study_id` |
| `core.imaging_series` | one DICOM series metadata row per study | `imaging_study_id` + `series_uid` |
| `core.organization` | one source organization | `organization_id` |
| `core.provider` | one source or claims provider | `provider_id` |
| `core.payer` | one claims payer | `payer_id` |
| `core.claim` | one claim header | `claim_id` |
| `core.claim_line` | one claim service line | `claim_line_id` |
| `core.claim_diagnosis` | one ordered diagnosis on a claim | `claim_id` + `diagnosis_sequence` |
| `core.claim_line_procedure` | one coded procedure on a claim line | `claim_line_id` + `code_system` + `code` |
| `core.claim_line_adjustment` | one reason-coded financial adjustment on a claim line | `claim_line_id` + group + reason |
| `core.hl7_observation` | one OBX result per HL7 message | `hl7_observation_id` |
| `core.hl7_encounter_event` | one controlled ADT lifecycle event | `hl7_encounter_event_id` |
| `core.hl7_order_event` | one order event per ORM message/order | `hl7_order_event_id` |
| `mart.ed_utilization_monthly` | reporting month | `reporting_month` |
| `mart.member_eligibility_monthly` | reporting month and payer organization | `reporting_month` + `payer_organization_id` |
| `mart.ed_utilization_eligible_monthly` | reporting month and payer organization | `reporting_month` + `payer_organization_id` |
| `mart.clinical_activity_monthly` | reporting month | `reporting_month` |
| `mart.claim_cost_monthly` | reporting month | `reporting_month` |
| `mart.lab_result_completeness_monthly` | laboratory result month | `reporting_month` |
| `mart.hl7_encounter_current_state` | one latest state per HL7 encounter | `encounter_id` |
| `mart.hl7_order_current_state` | one latest event per HL7 order | `order_id` |
| `mart.imaging_activity_monthly` | imaging study month | `reporting_month` |
| `omop.entity_id_map` | one stable integer ID per entity type/source ID | `entity_type` + `source_id` |
| `omop.person` | one qualified canonical patient | `person_id` |
| `omop.observation_period` | one non-overlapping observable period per person/island | `observation_period_id` |
| `omop.visit_occurrence` | one canonical encounter with a start timestamp | `visit_occurrence_id` |
| `omop.condition_occurrence` | one timestamped canonical condition | `condition_occurrence_id` |
| `omop.procedure_occurrence` | one timestamped canonical procedure | `procedure_occurrence_id` |
| `omop.measurement` | one timestamped canonical laboratory observation | `measurement_id` |
| `omop.drug_exposure` | one timestamped MedicationRequest order proxy | `drug_exposure_id` |
| `omop.payer_plan_period` | one active complete Coverage period | `payer_plan_period_id` |

The `omop` objects are v5.4-compatible extract views, not a conformant CDM instance. Most Standard Concept fields are deliberately `0`; consult `omop.source_to_standard_concept_status` before interpreting terminology.

`core.observation` retains source category and code, effective time, explicit value type, separate numeric/text/boolean/coded value fields, Quantity unit/system/code, documented absent reason, and the raw source-version key. Typed fields must not be coalesced when validating result completeness.

`core.coverage` retains status, patient and payer references, typed `coverage_start` and `coverage_end`, and the raw source-version key. The eligibility mart counts each distinct patient/payer/month once, even if defensive deduplication is needed.

`core.claim` carries payer and billing-provider keys, frequency/original-claim lineage, and financial totals. `core.claim_line` carries the rendering-provider key and line financials. Both retain paid, allowed, billed, patient-responsibility, and adjustment amounts so headers can be reconciled exactly to detail.
