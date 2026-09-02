-- Idempotent Phase 1 core loads. Run Patient before Encounter before Observation.
insert into core.patient (patient_id, birth_date, sex, source_raw_resource_id)
select patient_id, nullif(birth_date, '')::date, sex, raw_resource_id
from staging.stg_patient
on conflict (patient_id) do update
set birth_date = excluded.birth_date, sex = excluded.sex, source_raw_resource_id = excluded.source_raw_resource_id;

-- Preserve valid raw records with broken cross-resource references for investigation.
insert into quarantine.fhir_resource
    (run_id, source_system, resource_type, source_resource_id, payload, reason_code, reason_detail)
select r.run_id, r.source_system, r.resource_type, r.source_resource_id, r.payload,
       'UNRESOLVED_PATIENT_REFERENCE', 'Encounter subject does not resolve to a core patient'
from raw.fhir_resource r
join staging.stg_encounter s on s.raw_resource_id = r.raw_resource_id
left join core.patient p on p.patient_id = s.patient_id
where p.patient_id is null
on conflict do nothing;

insert into core.encounter (encounter_id, patient_id, encounter_status, encounter_class, start_at, end_at, source_raw_resource_id)
select encounter_id, patient_id, encounter_status, encounter_class,
       nullif(start_at, '')::timestamptz, nullif(end_at, '')::timestamptz, raw_resource_id
from staging.stg_encounter
where patient_id in (select patient_id from core.patient)
on conflict (encounter_id) do update
set patient_id = excluded.patient_id, encounter_status = excluded.encounter_status,
    encounter_class = excluded.encounter_class, start_at = excluded.start_at,
    end_at = excluded.end_at, source_raw_resource_id = excluded.source_raw_resource_id;

insert into quarantine.fhir_resource
    (run_id, source_system, resource_type, source_resource_id, payload, reason_code, reason_detail)
select r.run_id, r.source_system, r.resource_type, r.source_resource_id, r.payload,
       case when p.patient_id is null then 'UNRESOLVED_PATIENT_REFERENCE' else 'UNRESOLVED_ENCOUNTER_REFERENCE' end,
       case when p.patient_id is null then 'Observation subject does not resolve to a core patient' else 'Observation encounter does not resolve to a core encounter' end
from raw.fhir_resource r
join staging.stg_observation s on s.raw_resource_id = r.raw_resource_id
left join core.patient p on p.patient_id = s.patient_id
left join core.encounter e on e.encounter_id = s.encounter_id
where p.patient_id is null or (s.encounter_id is not null and e.encounter_id is null)
on conflict do nothing;

insert into core.observation
    (observation_id, patient_id, encounter_id, observation_status, coding_system, code,
     category_system, category_code, effective_at, value_type, value_numeric, value_text,
     value_boolean, value_code_system, value_code, value_code_display, unit, unit_system,
     unit_code, data_absent_reason_code, source_raw_resource_id)
select observation_id, patient_id, encounter_id, observation_status, coding_system, code,
       category_system, category_code, nullif(effective_at, '')::timestamptz, value_type,
       value_numeric, value_text, value_boolean, value_code_system, value_code,
       value_code_display, unit, unit_system, unit_code, data_absent_reason_code, raw_resource_id
from staging.stg_observation
where patient_id in (select patient_id from core.patient)
  and (encounter_id is null or encounter_id in (select encounter_id from core.encounter))
on conflict (observation_id) do update
set patient_id = excluded.patient_id, encounter_id = excluded.encounter_id,
    observation_status = excluded.observation_status, coding_system = excluded.coding_system,
    code = excluded.code, category_system = excluded.category_system,
    category_code = excluded.category_code, effective_at = excluded.effective_at,
    value_type = excluded.value_type, value_numeric = excluded.value_numeric,
    value_text = excluded.value_text, value_boolean = excluded.value_boolean,
    value_code_system = excluded.value_code_system, value_code = excluded.value_code,
    value_code_display = excluded.value_code_display, unit = excluded.unit,
    unit_system = excluded.unit_system, unit_code = excluded.unit_code,
    data_absent_reason_code = excluded.data_absent_reason_code,
    source_raw_resource_id = excluded.source_raw_resource_id;

insert into core.organization (organization_id, organization_name, organization_type_system, organization_type_code, source_raw_resource_id)
select organization_id, organization_name, type_system, type_code, raw_resource_id
from staging.stg_organization
on conflict (organization_id) do update
set organization_name = excluded.organization_name, organization_type_system = excluded.organization_type_system,
    organization_type_code = excluded.organization_type_code, source_raw_resource_id = excluded.source_raw_resource_id;

insert into core.provider (provider_id, provider_name, source_raw_resource_id)
select provider_id, provider_name, raw_resource_id
from staging.stg_practitioner
on conflict (provider_id) do update
set provider_name = excluded.provider_name, source_raw_resource_id = excluded.source_raw_resource_id;

insert into core.coverage
    (coverage_id, patient_id, payer_organization_id, coverage_status, source_raw_resource_id,
     coverage_start, coverage_end)
select coverage_id, patient_id, payer_organization_id, coverage_status, raw_resource_id,
       nullif(coverage_start, '')::date, nullif(coverage_end, '')::date
from staging.stg_coverage
where patient_id in (select patient_id from core.patient)
  and (payer_organization_id is null or payer_organization_id in (select organization_id from core.organization))
on conflict (coverage_id) do update
set patient_id = excluded.patient_id, payer_organization_id = excluded.payer_organization_id,
    coverage_status = excluded.coverage_status, source_raw_resource_id = excluded.source_raw_resource_id,
    coverage_start = excluded.coverage_start, coverage_end = excluded.coverage_end;

insert into quarantine.fhir_resource
    (run_id, source_system, resource_type, source_resource_id, payload, reason_code, reason_detail)
select raw.run_id, raw.source_system, raw.resource_type, raw.source_resource_id, raw.payload,
       case when patient.patient_id is null then 'UNRESOLVED_PATIENT_REFERENCE' else 'UNRESOLVED_ENCOUNTER_REFERENCE' end,
       'ImagingStudy reference does not resolve to the canonical clinical model'
from raw.fhir_resource raw
join staging.stg_imaging_study study on study.raw_resource_id = raw.raw_resource_id
left join core.patient patient on patient.patient_id = study.patient_id
left join core.encounter encounter on encounter.encounter_id = study.encounter_id
where patient.patient_id is null or (study.encounter_id is not null and encounter.encounter_id is null)
on conflict do nothing;

insert into core.imaging_study
    (imaging_study_id, patient_id, encounter_id, study_status, started_at, study_uid,
     accession_identifier, number_of_series, number_of_instances, source_raw_resource_id)
select imaging_study_id, patient_id, encounter_id, study_status, started_at::timestamptz,
       study_uid, accession_identifier, number_of_series, number_of_instances, raw_resource_id
from staging.stg_imaging_study
where patient_id in (select patient_id from core.patient)
  and (encounter_id is null or encounter_id in (select encounter_id from core.encounter))
on conflict (imaging_study_id) do update
set patient_id = excluded.patient_id, encounter_id = excluded.encounter_id,
    study_status = excluded.study_status, started_at = excluded.started_at,
    study_uid = excluded.study_uid, accession_identifier = excluded.accession_identifier,
    number_of_series = excluded.number_of_series, number_of_instances = excluded.number_of_instances,
    source_raw_resource_id = excluded.source_raw_resource_id;

delete from core.imaging_series series
using staging.stg_imaging_study study
where series.imaging_study_id = study.imaging_study_id;

insert into core.imaging_series
    (imaging_study_id, series_uid, series_number, modality_system, modality_code,
     body_site_system, body_site_code, number_of_instances)
select series.imaging_study_id, series.series_uid, series.series_number,
       series.modality_system, series.modality_code, series.body_site_system,
       series.body_site_code, series.number_of_instances
from staging.stg_imaging_series series
join core.imaging_study study on study.imaging_study_id = series.imaging_study_id;

insert into core.condition_occurrence (condition_id, patient_id, encounter_id, clinical_status, coding_system, code, recorded_at, source_raw_resource_id)
select condition_id, patient_id, encounter_id, clinical_status, coding_system, code, nullif(recorded_at, '')::timestamptz, raw_resource_id
from staging.stg_condition
where patient_id in (select patient_id from core.patient)
  and (encounter_id is null or encounter_id in (select encounter_id from core.encounter))
on conflict (condition_id) do update
set patient_id = excluded.patient_id, encounter_id = excluded.encounter_id, clinical_status = excluded.clinical_status,
    coding_system = excluded.coding_system, code = excluded.code, recorded_at = excluded.recorded_at,
    source_raw_resource_id = excluded.source_raw_resource_id;

insert into core.procedure_occurrence (procedure_id, patient_id, encounter_id, procedure_status, coding_system, code, performed_at, source_raw_resource_id)
select procedure_id, patient_id, encounter_id, procedure_status, coding_system, code, nullif(performed_at, '')::timestamptz, raw_resource_id
from staging.stg_procedure
where patient_id in (select patient_id from core.patient)
  and (encounter_id is null or encounter_id in (select encounter_id from core.encounter))
on conflict (procedure_id) do update
set patient_id = excluded.patient_id, encounter_id = excluded.encounter_id, procedure_status = excluded.procedure_status,
    coding_system = excluded.coding_system, code = excluded.code, performed_at = excluded.performed_at,
    source_raw_resource_id = excluded.source_raw_resource_id;

insert into core.medication_request (medication_request_id, patient_id, encounter_id, medication_status, coding_system, code, authored_at, source_raw_resource_id)
select medication_request_id, patient_id, encounter_id, medication_status, coding_system, code, nullif(authored_at, '')::timestamptz, raw_resource_id
from staging.stg_medication_request
where patient_id in (select patient_id from core.patient)
  and (encounter_id is null or encounter_id in (select encounter_id from core.encounter))
on conflict (medication_request_id) do update
set patient_id = excluded.patient_id, encounter_id = excluded.encounter_id, medication_status = excluded.medication_status,
    coding_system = excluded.coding_system, code = excluded.code, authored_at = excluded.authored_at,
    source_raw_resource_id = excluded.source_raw_resource_id;
