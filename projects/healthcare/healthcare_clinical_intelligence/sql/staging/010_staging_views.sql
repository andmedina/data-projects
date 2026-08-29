create schema if not exists staging;

create or replace view staging.stg_patient as
select source_resource_id as patient_id,
       payload ->> 'birthDate' as birth_date,
       payload ->> 'gender' as sex,
       raw_resource_id
from raw.fhir_resource
where resource_type = 'Patient';

create or replace view staging.stg_encounter as
select source_resource_id as encounter_id,
       regexp_replace(payload #>> '{subject,reference}', '^.*/', '') as patient_id,
       payload ->> 'status' as encounter_status,
       payload #>> '{class,code}' as encounter_class,
       payload #>> '{period,start}' as start_at,
       payload #>> '{period,end}' as end_at,
       raw_resource_id
from raw.fhir_resource
where resource_type = 'Encounter';

create or replace view staging.stg_observation as
select source_resource_id as observation_id,
       regexp_replace(payload #>> '{subject,reference}', '^.*/', '') as patient_id,
       regexp_replace(payload #>> '{encounter,reference}', '^.*/', '') as encounter_id,
       payload ->> 'status' as observation_status,
       payload #>> '{code,coding,0,system}' as coding_system,
       payload #>> '{code,coding,0,code}' as code,
       payload ->> 'effectiveDateTime' as effective_at,
       raw_resource_id
from raw.fhir_resource
where resource_type = 'Observation';
