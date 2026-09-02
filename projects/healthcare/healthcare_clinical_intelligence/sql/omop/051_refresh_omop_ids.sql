insert into omop.entity_id_map (entity_type, source_id)
select entity_type, source_id
from (
    select 'person'::text as entity_type, patient_id as source_id
    from core.patient
    where birth_date is not null
    union all
    select 'observation_period', source_id
    from omop.observation_period_source
    union all
    select 'visit_occurrence', encounter_id
    from core.encounter
    where start_at is not null
    union all
    select 'condition_occurrence', condition_id
    from core.condition_occurrence
    where recorded_at is not null
    union all
    select 'procedure_occurrence', procedure_id
    from core.procedure_occurrence
    where performed_at is not null
    union all
    select 'measurement', observation_id
    from core.observation
    where category_code = 'laboratory'
      and effective_at is not null
    union all
    select 'drug_exposure', medication_request_id
    from core.medication_request
    where authored_at is not null
    union all
    select 'payer_plan_period', coverage_id
    from core.coverage
    where coverage_status = 'active'
      and coverage_start is not null
      and coverage_end is not null
) source_entity
order by entity_type, source_id
on conflict (entity_type, source_id) do nothing;
