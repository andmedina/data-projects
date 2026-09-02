-- DE-009 independent validation. Exception queries must return zero rows.

-- Source-to-view counts for all implemented domains.
select domain_name,
       source_rows,
       omop_rows,
       source_rows - omop_rows as row_difference
from omop.domain_row_count
order by domain_name;

-- Every domain must reconcile exactly.
select domain_name, source_rows, omop_rows
from omop.domain_row_count
where source_rows <> omop_rows;

-- Implemented views must retain the selected OMOP CDM v5.4 column shapes.
with expected(table_name, expected_columns) as (
    values
        ('person', 18),
        ('observation_period', 5),
        ('visit_occurrence', 17),
        ('condition_occurrence', 16),
        ('procedure_occurrence', 16),
        ('measurement', 23),
        ('drug_exposure', 23),
        ('payer_plan_period', 17)
),
actual as (
    select table_name, count(*) as actual_columns
    from information_schema.columns
    where table_schema = 'omop'
    group by table_name
)
select expected.table_name,
       expected.expected_columns,
       coalesce(actual.actual_columns, 0) as actual_columns
from expected
left join actual using (table_name)
where expected.expected_columns <> coalesce(actual.actual_columns, 0);

-- Every PERSON requires at least one OBSERVATION_PERIOD.
select person.person_id, person.person_source_value
from omop.person person
left join omop.observation_period period on period.person_id = person.person_id
where period.observation_period_id is null;

-- Observation periods for one person must not overlap or be adjacent after merging.
with ordered_period as (
    select period.*,
           lag(observation_period_end_date) over (
               partition by person_id
               order by observation_period_start_date, observation_period_id
           ) as prior_period_end_date
    from omop.observation_period period
)
select observation_period_id,
       person_id,
       observation_period_start_date,
       prior_period_end_date
from ordered_period
where observation_period_start_date <= prior_period_end_date + 1;

-- All event PERSON keys and populated VISIT_OCCURRENCE keys must resolve.
select domain_name, event_id
from (
    select 'visit_occurrence'::text as domain_name, visit.visit_occurrence_id as event_id
    from omop.visit_occurrence visit
    left join omop.person person on person.person_id = visit.person_id
    where person.person_id is null
    union all
    select 'condition_occurrence', condition.condition_occurrence_id
    from omop.condition_occurrence condition
    left join omop.person person on person.person_id = condition.person_id
    left join omop.visit_occurrence visit on visit.visit_occurrence_id = condition.visit_occurrence_id
    where person.person_id is null
       or (condition.visit_occurrence_id is not null and visit.visit_occurrence_id is null)
    union all
    select 'procedure_occurrence', procedure.procedure_occurrence_id
    from omop.procedure_occurrence procedure
    left join omop.person person on person.person_id = procedure.person_id
    left join omop.visit_occurrence visit on visit.visit_occurrence_id = procedure.visit_occurrence_id
    where person.person_id is null
       or (procedure.visit_occurrence_id is not null and visit.visit_occurrence_id is null)
    union all
    select 'measurement', measurement.measurement_id
    from omop.measurement measurement
    left join omop.person person on person.person_id = measurement.person_id
    left join omop.visit_occurrence visit on visit.visit_occurrence_id = measurement.visit_occurrence_id
    where person.person_id is null
       or (measurement.visit_occurrence_id is not null and visit.visit_occurrence_id is null)
    union all
    select 'drug_exposure', drug.drug_exposure_id
    from omop.drug_exposure drug
    left join omop.person person on person.person_id = drug.person_id
    left join omop.visit_occurrence visit on visit.visit_occurrence_id = drug.visit_occurrence_id
    where person.person_id is null
       or (drug.visit_occurrence_id is not null and visit.visit_occurrence_id is null)
    union all
    select 'payer_plan_period', payer.payer_plan_period_id
    from omop.payer_plan_period payer
    left join omop.person person on person.person_id = payer.person_id
    where person.person_id is null
) orphan_event;

-- OMOP IDs must be unique within each implemented entity type.
select entity_type, omop_id, count(*) as duplicate_rows
from omop.entity_id_map
group by entity_type, omop_id
having count(*) > 1;

-- Controlled Encounter classes must never fall through to concept 0.
select visit_source_value, visit_concept_id, count(*) as visits
from omop.visit_occurrence
where visit_source_value in ('IMP', 'AMB', 'EMER')
  and visit_concept_id = 0
group by visit_source_value, visit_concept_id;

-- Informational vocabulary backlog; rows are expected until Athena governance is added.
select domain_id,
       source_vocabulary,
       source_code,
       target_concept_id,
       source_rows,
       mapped_to_standard
from omop.source_to_standard_concept_status
order by mapped_to_standard, domain_id, source_vocabulary, source_code;
