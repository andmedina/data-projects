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

insert into core.observation (observation_id, patient_id, encounter_id, observation_status, coding_system, code, effective_at, source_raw_resource_id)
select observation_id, patient_id, encounter_id, observation_status, coding_system, code,
       nullif(effective_at, '')::timestamptz, raw_resource_id
from staging.stg_observation
where patient_id in (select patient_id from core.patient)
  and (encounter_id is null or encounter_id in (select encounter_id from core.encounter))
on conflict (observation_id) do update
set patient_id = excluded.patient_id, encounter_id = excluded.encounter_id,
    observation_status = excluded.observation_status, coding_system = excluded.coding_system,
    code = excluded.code, effective_at = excluded.effective_at,
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

insert into core.coverage (coverage_id, patient_id, payer_organization_id, coverage_status, source_raw_resource_id)
select coverage_id, patient_id, payer_organization_id, coverage_status, raw_resource_id
from staging.stg_coverage
where patient_id in (select patient_id from core.patient)
  and (payer_organization_id is null or payer_organization_id in (select organization_id from core.organization))
on conflict (coverage_id) do update
set patient_id = excluded.patient_id, payer_organization_id = excluded.payer_organization_id,
    coverage_status = excluded.coverage_status, source_raw_resource_id = excluded.source_raw_resource_id;

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
