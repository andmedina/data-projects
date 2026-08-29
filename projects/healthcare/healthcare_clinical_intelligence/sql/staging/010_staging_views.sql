create schema if not exists staging;

create or replace view staging.stg_patient as
with latest_resource as (
    select *, row_number() over (
        partition by resource_type, source_resource_id
        order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc
    ) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as patient_id,
       payload ->> 'birthDate' as birth_date,
       payload ->> 'gender' as sex,
       raw_resource_id
from latest_resource
where resource_type = 'Patient' and source_version_rank = 1;

create or replace view staging.stg_encounter as
with latest_resource as (
    select *, row_number() over (
        partition by resource_type, source_resource_id
        order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc
    ) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as encounter_id,
       regexp_replace(payload #>> '{subject,reference}', '^.*/', '') as patient_id,
       payload ->> 'status' as encounter_status,
       payload #>> '{class,code}' as encounter_class,
       payload #>> '{period,start}' as start_at,
       payload #>> '{period,end}' as end_at,
       raw_resource_id
from latest_resource
where resource_type = 'Encounter' and source_version_rank = 1;

create or replace view staging.stg_observation as
with latest_resource as (
    select *, row_number() over (
        partition by resource_type, source_resource_id
        order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc
    ) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as observation_id,
       regexp_replace(payload #>> '{subject,reference}', '^.*/', '') as patient_id,
       regexp_replace(payload #>> '{encounter,reference}', '^.*/', '') as encounter_id,
       payload ->> 'status' as observation_status,
       payload #>> '{code,coding,0,system}' as coding_system,
       payload #>> '{code,coding,0,code}' as code,
       payload ->> 'effectiveDateTime' as effective_at,
       raw_resource_id
from latest_resource
where resource_type = 'Observation' and source_version_rank = 1;

create or replace view staging.stg_organization as
with latest_resource as (
    select *, row_number() over (partition by resource_type, source_resource_id order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as organization_id, payload ->> 'name' as organization_name,
       payload #>> '{type,0,coding,0,system}' as type_system, payload #>> '{type,0,coding,0,code}' as type_code, raw_resource_id
from latest_resource where resource_type = 'Organization' and source_version_rank = 1;

create or replace view staging.stg_practitioner as
with latest_resource as (
    select *, row_number() over (partition by resource_type, source_resource_id order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as provider_id,
       concat_ws(' ', payload #>> '{name,0,given,0}', payload #>> '{name,0,family}') as provider_name, raw_resource_id
from latest_resource where resource_type = 'Practitioner' and source_version_rank = 1;

create or replace view staging.stg_coverage as
with latest_resource as (
    select *, row_number() over (partition by resource_type, source_resource_id order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as coverage_id, regexp_replace(payload #>> '{beneficiary,reference}', '^.*/', '') as patient_id,
       regexp_replace(payload #>> '{payor,0,reference}', '^.*/', '') as payer_organization_id, payload ->> 'status' as coverage_status, raw_resource_id
from latest_resource where resource_type = 'Coverage' and source_version_rank = 1;

create or replace view staging.stg_condition as
with latest_resource as (
    select *, row_number() over (partition by resource_type, source_resource_id order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as condition_id, regexp_replace(payload #>> '{subject,reference}', '^.*/', '') as patient_id,
       regexp_replace(payload #>> '{encounter,reference}', '^.*/', '') as encounter_id,
       payload #>> '{clinicalStatus,coding,0,code}' as clinical_status, payload #>> '{code,coding,0,system}' as coding_system,
       payload #>> '{code,coding,0,code}' as code, payload ->> 'recordedDate' as recorded_at, raw_resource_id
from latest_resource where resource_type = 'Condition' and source_version_rank = 1;

create or replace view staging.stg_procedure as
with latest_resource as (
    select *, row_number() over (partition by resource_type, source_resource_id order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as procedure_id, regexp_replace(payload #>> '{subject,reference}', '^.*/', '') as patient_id,
       regexp_replace(payload #>> '{encounter,reference}', '^.*/', '') as encounter_id,
       payload ->> 'status' as procedure_status, payload #>> '{code,coding,0,system}' as coding_system,
       payload #>> '{code,coding,0,code}' as code, payload ->> 'performedDateTime' as performed_at, raw_resource_id
from latest_resource where resource_type = 'Procedure' and source_version_rank = 1;

create or replace view staging.stg_medication_request as
with latest_resource as (
    select *, row_number() over (partition by resource_type, source_resource_id order by last_updated_at desc nulls last, ingested_at desc, raw_resource_id desc) as source_version_rank
    from raw.fhir_resource
)
select source_resource_id as medication_request_id, regexp_replace(payload #>> '{subject,reference}', '^.*/', '') as patient_id,
       regexp_replace(payload #>> '{encounter,reference}', '^.*/', '') as encounter_id,
       payload ->> 'status' as medication_status, payload #>> '{medicationCodeableConcept,coding,0,system}' as coding_system,
       payload #>> '{medicationCodeableConcept,coding,0,code}' as code, payload ->> 'authoredOn' as authored_at, raw_resource_id
from latest_resource where resource_type = 'MedicationRequest' and source_version_rank = 1;

create or replace view staging.stg_claim_line as
select source_claim_id as claim_id, source_claim_line_id as claim_line_id,
       payload ->> 'patient_id' as patient_id, (payload ->> 'service_date')::date as service_date,
       (payload ->> 'billed_amount')::numeric(14,2) as billed_amount,
       (payload ->> 'allowed_amount')::numeric(14,2) as allowed_amount,
       (payload ->> 'paid_amount')::numeric(14,2) as paid_amount,
       raw_claim_line_id
from raw.claim_line;
