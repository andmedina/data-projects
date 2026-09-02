create schema if not exists omop;

create table if not exists omop.entity_id_map (
    entity_type text not null,
    source_id text not null,
    omop_id integer generated always as identity,
    created_at timestamptz not null default current_timestamp,
    primary key (entity_type, source_id),
    unique (entity_type, omop_id)
);

create or replace view omop.observation_period_source as
with eligible_period as (
    select coverage_id,
           patient_id,
           coverage_start,
           coverage_end
    from core.coverage
    where coverage_status = 'active'
      and coverage_start is not null
      and coverage_end is not null
),
ordered_period as (
    select *,
           max(coverage_end) over (
               partition by patient_id
               order by coverage_start, coverage_end, coverage_id
               rows between unbounded preceding and 1 preceding
           ) as prior_max_end
    from eligible_period
),
island_numbered as (
    select *,
           sum(
               case
                   when prior_max_end is null or coverage_start > prior_max_end + 1 then 1
                   else 0
               end
           ) over (
               partition by patient_id
               order by coverage_start, coverage_end, coverage_id
           ) as period_island
    from ordered_period
),
merged_period as (
    select patient_id,
           min(coverage_start) as observation_period_start_date,
           max(coverage_end) as observation_period_end_date
    from island_numbered
    group by patient_id, period_island
),
clinical_event_date as (
    select patient_id, start_at::date as event_date from core.encounter where start_at is not null
    union all
    select patient_id, effective_at::date from core.observation where effective_at is not null
    union all
    select patient_id, recorded_at::date from core.condition_occurrence where recorded_at is not null
    union all
    select patient_id, performed_at::date from core.procedure_occurrence where performed_at is not null
    union all
    select patient_id, authored_at::date from core.medication_request where authored_at is not null
),
clinical_span as (
    select patient_id,
           min(event_date) as observation_period_start_date,
           max(event_date) as observation_period_end_date
    from clinical_event_date
    group by patient_id
),
combined_period as (
    select patient_id,
           observation_period_start_date,
           observation_period_end_date,
           'active_coverage'::text as period_provenance
    from merged_period
    union all
    select clinical.patient_id,
           clinical.observation_period_start_date,
           clinical.observation_period_end_date,
           'clinical_event_span'::text
    from clinical_span clinical
    where not exists (
        select 1 from merged_period coverage
        where coverage.patient_id = clinical.patient_id
    )
)
select patient_id,
       observation_period_start_date,
       observation_period_end_date,
       concat(
           patient_id, '|', observation_period_start_date::text, '|',
           observation_period_end_date::text
       ) as source_id,
       period_provenance
from combined_period;

create or replace view omop.person as
select person_map.omop_id as person_id,
       0::integer as gender_concept_id,
       extract(year from patient.birth_date)::integer as year_of_birth,
       extract(month from patient.birth_date)::integer as month_of_birth,
       extract(day from patient.birth_date)::integer as day_of_birth,
       patient.birth_date::timestamp as birth_datetime,
       0::integer as race_concept_id,
       0::integer as ethnicity_concept_id,
       null::integer as location_id,
       null::integer as provider_id,
       null::integer as care_site_id,
       left(patient.patient_id, 50)::varchar(50) as person_source_value,
       left(patient.sex, 50)::varchar(50) as gender_source_value,
       0::integer as gender_source_concept_id,
       null::varchar(50) as race_source_value,
       0::integer as race_source_concept_id,
       null::varchar(50) as ethnicity_source_value,
       0::integer as ethnicity_source_concept_id
from core.patient patient
join omop.entity_id_map person_map
  on person_map.entity_type = 'person'
 and person_map.source_id = patient.patient_id
where patient.birth_date is not null;

create or replace view omop.observation_period as
select period_map.omop_id as observation_period_id,
       person_map.omop_id as person_id,
       source.observation_period_start_date,
       source.observation_period_end_date,
       0::integer as period_type_concept_id
from omop.observation_period_source source
join omop.entity_id_map period_map
  on period_map.entity_type = 'observation_period'
 and period_map.source_id = source.source_id
join omop.entity_id_map person_map
  on person_map.entity_type = 'person'
 and person_map.source_id = source.patient_id;

create or replace view omop.visit_occurrence as
with visit_source as (
    select encounter.*,
           lag(encounter.encounter_id) over (
               partition by encounter.patient_id
               order by encounter.start_at, encounter.encounter_id
           ) as preceding_encounter_id
    from core.encounter encounter
    where encounter.start_at is not null
)
select visit_map.omop_id as visit_occurrence_id,
       person_map.omop_id as person_id,
       case visit.encounter_class
           when 'IMP' then 9201
           when 'AMB' then 9202
           when 'EMER' then 9203
           else 0
       end::integer as visit_concept_id,
       visit.start_at::date as visit_start_date,
       visit.start_at at time zone 'UTC' as visit_start_datetime,
       coalesce(visit.end_at, visit.start_at)::date as visit_end_date,
       coalesce(visit.end_at, visit.start_at) at time zone 'UTC' as visit_end_datetime,
       0::integer as visit_type_concept_id,
       null::integer as provider_id,
       null::integer as care_site_id,
       left(visit.encounter_class, 50)::varchar(50) as visit_source_value,
       0::integer as visit_source_concept_id,
       0::integer as admitted_from_concept_id,
       null::varchar(50) as admitted_from_source_value,
       0::integer as discharged_to_concept_id,
       null::varchar(50) as discharged_to_source_value,
       preceding_map.omop_id as preceding_visit_occurrence_id
from visit_source visit
join omop.entity_id_map visit_map
  on visit_map.entity_type = 'visit_occurrence'
 and visit_map.source_id = visit.encounter_id
join omop.entity_id_map person_map
  on person_map.entity_type = 'person'
 and person_map.source_id = visit.patient_id
left join omop.entity_id_map preceding_map
  on preceding_map.entity_type = 'visit_occurrence'
 and preceding_map.source_id = visit.preceding_encounter_id;

create or replace view omop.condition_occurrence as
select condition_map.omop_id as condition_occurrence_id,
       person_map.omop_id as person_id,
       0::integer as condition_concept_id,
       condition.recorded_at::date as condition_start_date,
       condition.recorded_at at time zone 'UTC' as condition_start_datetime,
       null::date as condition_end_date,
       null::timestamp as condition_end_datetime,
       0::integer as condition_type_concept_id,
       0::integer as condition_status_concept_id,
       null::varchar(20) as stop_reason,
       null::integer as provider_id,
       visit_map.omop_id as visit_occurrence_id,
       null::integer as visit_detail_id,
       left(condition.code, 50)::varchar(50) as condition_source_value,
       0::integer as condition_source_concept_id,
       left(condition.clinical_status, 50)::varchar(50) as condition_status_source_value
from core.condition_occurrence condition
join omop.entity_id_map condition_map
  on condition_map.entity_type = 'condition_occurrence'
 and condition_map.source_id = condition.condition_id
join omop.entity_id_map person_map
  on person_map.entity_type = 'person'
 and person_map.source_id = condition.patient_id
left join omop.entity_id_map visit_map
  on visit_map.entity_type = 'visit_occurrence'
 and visit_map.source_id = condition.encounter_id
where condition.recorded_at is not null;

create or replace view omop.procedure_occurrence as
select procedure_map.omop_id as procedure_occurrence_id,
       person_map.omop_id as person_id,
       0::integer as procedure_concept_id,
       procedure.performed_at::date as procedure_date,
       procedure.performed_at at time zone 'UTC' as procedure_datetime,
       null::date as procedure_end_date,
       null::timestamp as procedure_end_datetime,
       0::integer as procedure_type_concept_id,
       0::integer as modifier_concept_id,
       1::integer as quantity,
       null::integer as provider_id,
       visit_map.omop_id as visit_occurrence_id,
       null::integer as visit_detail_id,
       left(procedure.code, 50)::varchar(50) as procedure_source_value,
       0::integer as procedure_source_concept_id,
       null::varchar(50) as modifier_source_value
from core.procedure_occurrence procedure
join omop.entity_id_map procedure_map
  on procedure_map.entity_type = 'procedure_occurrence'
 and procedure_map.source_id = procedure.procedure_id
join omop.entity_id_map person_map
  on person_map.entity_type = 'person'
 and person_map.source_id = procedure.patient_id
left join omop.entity_id_map visit_map
  on visit_map.entity_type = 'visit_occurrence'
 and visit_map.source_id = procedure.encounter_id
where procedure.performed_at is not null;

create or replace view omop.measurement as
select measurement_map.omop_id as measurement_id,
       person_map.omop_id as person_id,
       0::integer as measurement_concept_id,
       observation.effective_at::date as measurement_date,
       observation.effective_at at time zone 'UTC' as measurement_datetime,
       null::varchar(10) as measurement_time,
       0::integer as measurement_type_concept_id,
       null::integer as operator_concept_id,
       observation.value_numeric as value_as_number,
       0::integer as value_as_concept_id,
       0::integer as unit_concept_id,
       null::numeric as range_low,
       null::numeric as range_high,
       null::integer as provider_id,
       visit_map.omop_id as visit_occurrence_id,
       null::integer as visit_detail_id,
       left(observation.code, 50)::varchar(50) as measurement_source_value,
       0::integer as measurement_source_concept_id,
       left(observation.unit_code, 50)::varchar(50) as unit_source_value,
       0::integer as unit_source_concept_id,
       left(
           coalesce(
               observation.value_text,
               observation.value_code_display,
               observation.value_boolean::text,
               observation.value_numeric::text,
               observation.data_absent_reason_code
           ),
           50
       )::varchar(50) as value_source_value,
       null::bigint as measurement_event_id,
       null::integer as meas_event_field_concept_id
from core.observation observation
join omop.entity_id_map measurement_map
  on measurement_map.entity_type = 'measurement'
 and measurement_map.source_id = observation.observation_id
join omop.entity_id_map person_map
  on person_map.entity_type = 'person'
 and person_map.source_id = observation.patient_id
left join omop.entity_id_map visit_map
  on visit_map.entity_type = 'visit_occurrence'
 and visit_map.source_id = observation.encounter_id
where observation.category_code = 'laboratory'
  and observation.effective_at is not null;

create or replace view omop.drug_exposure as
select drug_map.omop_id as drug_exposure_id,
       person_map.omop_id as person_id,
       0::integer as drug_concept_id,
       medication.authored_at::date as drug_exposure_start_date,
       medication.authored_at at time zone 'UTC' as drug_exposure_start_datetime,
       medication.authored_at::date as drug_exposure_end_date,
       medication.authored_at at time zone 'UTC' as drug_exposure_end_datetime,
       null::date as verbatim_end_date,
       0::integer as drug_type_concept_id,
       null::varchar(20) as stop_reason,
       null::integer as refills,
       null::numeric as quantity,
       null::integer as days_supply,
       null::text as sig,
       0::integer as route_concept_id,
       null::varchar(50) as lot_number,
       null::integer as provider_id,
       visit_map.omop_id as visit_occurrence_id,
       null::integer as visit_detail_id,
       left(medication.code, 50)::varchar(50) as drug_source_value,
       0::integer as drug_source_concept_id,
       null::varchar(50) as route_source_value,
       null::varchar(50) as dose_unit_source_value
from core.medication_request medication
join omop.entity_id_map drug_map
  on drug_map.entity_type = 'drug_exposure'
 and drug_map.source_id = medication.medication_request_id
join omop.entity_id_map person_map
  on person_map.entity_type = 'person'
 and person_map.source_id = medication.patient_id
left join omop.entity_id_map visit_map
  on visit_map.entity_type = 'visit_occurrence'
 and visit_map.source_id = medication.encounter_id
where medication.authored_at is not null;

create or replace view omop.payer_plan_period as
select payer_plan_map.omop_id as payer_plan_period_id,
       person_map.omop_id as person_id,
       coverage.coverage_start as payer_plan_period_start_date,
       coverage.coverage_end as payer_plan_period_end_date,
       0::integer as payer_concept_id,
       left(coverage.payer_organization_id, 50)::varchar(50) as payer_source_value,
       0::integer as payer_source_concept_id,
       0::integer as plan_concept_id,
       null::varchar(50) as plan_source_value,
       0::integer as plan_source_concept_id,
       0::integer as sponsor_concept_id,
       null::varchar(50) as sponsor_source_value,
       0::integer as sponsor_source_concept_id,
       null::varchar(50) as family_source_value,
       0::integer as stop_reason_concept_id,
       null::varchar(50) as stop_reason_source_value,
       0::integer as stop_reason_source_concept_id
from core.coverage coverage
join omop.entity_id_map payer_plan_map
  on payer_plan_map.entity_type = 'payer_plan_period'
 and payer_plan_map.source_id = coverage.coverage_id
join omop.entity_id_map person_map
  on person_map.entity_type = 'person'
 and person_map.source_id = coverage.patient_id
where coverage.coverage_status = 'active'
  and coverage.coverage_start is not null
  and coverage.coverage_end is not null;

create or replace view omop.source_to_standard_concept_status as
with source_code as (
    select 'Visit'::text as domain_id,
           'FHIR Encounter.class'::text as source_vocabulary,
           encounter_class as source_code,
           case encounter_class
               when 'IMP' then 9201
               when 'AMB' then 9202
               when 'EMER' then 9203
               else 0
           end::integer as target_concept_id
    from core.encounter
    where encounter_class is not null
    union all
    select 'Condition', coding_system, code, 0 from core.condition_occurrence where code is not null
    union all
    select 'Procedure', coding_system, code, 0 from core.procedure_occurrence where code is not null
    union all
    select 'Measurement', coding_system, code, 0 from core.observation
    where category_code = 'laboratory' and code is not null
    union all
    select 'Drug', coding_system, code, 0 from core.medication_request where code is not null
)
select domain_id,
       source_vocabulary,
       source_code,
       target_concept_id,
       count(*) as source_rows,
       (target_concept_id <> 0) as mapped_to_standard
from source_code
group by domain_id, source_vocabulary, source_code, target_concept_id;

create or replace view omop.domain_row_count as
select 'person'::text as domain_name,
       (select count(*) from core.patient where birth_date is not null) as source_rows,
       (select count(*) from omop.person) as omop_rows
union all
select 'observation_period',
       (select count(*) from omop.observation_period_source),
       (select count(*) from omop.observation_period)
union all
select 'visit_occurrence',
       (select count(*) from core.encounter where start_at is not null),
       (select count(*) from omop.visit_occurrence)
union all
select 'condition_occurrence',
       (select count(*) from core.condition_occurrence where recorded_at is not null),
       (select count(*) from omop.condition_occurrence)
union all
select 'procedure_occurrence',
       (select count(*) from core.procedure_occurrence where performed_at is not null),
       (select count(*) from omop.procedure_occurrence)
union all
select 'measurement',
       (select count(*) from core.observation where category_code = 'laboratory' and effective_at is not null),
       (select count(*) from omop.measurement)
union all
select 'drug_exposure',
       (select count(*) from core.medication_request where authored_at is not null),
       (select count(*) from omop.drug_exposure)
union all
select 'payer_plan_period',
       (select count(*) from core.coverage where coverage_status = 'active' and coverage_start is not null and coverage_end is not null),
       (select count(*) from omop.payer_plan_period);
