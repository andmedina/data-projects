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
       raw_resource_id,
       payload #>> '{category,0,coding,0,system}' as category_system,
       payload #>> '{category,0,coding,0,code}' as category_code,
       case
           when payload ? 'valueQuantity' then 'Quantity'
           when payload ? 'valueString' then 'String'
           when payload ? 'valueBoolean' then 'Boolean'
           when payload ? 'valueInteger' then 'Integer'
           when payload ? 'valueCodeableConcept' then 'CodeableConcept'
       end as value_type,
       case
           when payload ? 'valueQuantity'
                and payload #>> '{valueQuantity,value}' ~ '^-?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?$'
               then (payload #>> '{valueQuantity,value}')::numeric
           when payload ? 'valueInteger'
                and payload ->> 'valueInteger' ~ '^-?[0-9]+$'
               then (payload ->> 'valueInteger')::numeric
       end as value_numeric,
       payload ->> 'valueString' as value_text,
       case when payload ? 'valueBoolean' then (payload ->> 'valueBoolean')::boolean end as value_boolean,
       payload #>> '{valueCodeableConcept,coding,0,system}' as value_code_system,
       payload #>> '{valueCodeableConcept,coding,0,code}' as value_code,
       coalesce(payload #>> '{valueCodeableConcept,coding,0,display}', payload #>> '{valueCodeableConcept,text}') as value_code_display,
       payload #>> '{valueQuantity,unit}' as unit,
       payload #>> '{valueQuantity,system}' as unit_system,
       payload #>> '{valueQuantity,code}' as unit_code,
       payload #>> '{dataAbsentReason,coding,0,code}' as data_absent_reason_code
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
with latest_claim_line as (
    select *,
           row_number() over (
               partition by source_system, source_claim_line_id
               order by raw_claim_line_id desc
           ) as source_version_rank
    from raw.claim_line
)
select source_claim_id as claim_id, source_claim_line_id as claim_line_id,
       payload ->> 'patient_id' as patient_id, (payload ->> 'service_date')::date as service_date,
       (payload ->> 'billed_amount')::numeric(14,2) as billed_amount,
       (payload ->> 'allowed_amount')::numeric(14,2) as allowed_amount,
       (payload ->> 'paid_amount')::numeric(14,2) as paid_amount,
       raw_claim_line_id,
       source_system,
       payload ->> 'payer_id' as payer_id,
       payload ->> 'payer_name' as payer_name,
       payload ->> 'billing_provider_id' as billing_provider_id,
       payload ->> 'billing_provider_npi' as billing_provider_npi,
       payload ->> 'billing_provider_name' as billing_provider_name,
       payload ->> 'rendering_provider_id' as rendering_provider_id,
       payload ->> 'rendering_provider_npi' as rendering_provider_npi,
       payload ->> 'rendering_provider_name' as rendering_provider_name,
       payload ->> 'diagnosis_codes' as diagnosis_codes,
       payload ->> 'procedure_code_system' as procedure_code_system,
       payload ->> 'procedure_code' as procedure_code,
       coalesce(nullif(payload ->> 'claim_frequency_code', ''), '1') as claim_frequency_code,
       nullif(payload ->> 'original_claim_id', '') as original_claim_id,
       coalesce(nullif(payload ->> 'patient_responsibility_amount', '')::numeric(14,2), 0) as patient_responsibility_amount,
       payload ->> 'adjustment_group_code' as adjustment_group_code,
       payload ->> 'adjustment_reason_code' as adjustment_reason_code,
       coalesce(nullif(payload ->> 'adjustment_amount', '')::numeric(14,2), 0) as adjustment_amount
from latest_claim_line
where source_version_rank = 1;
