create or replace view mart.clinical_activity_monthly as
with activity as (
    select date_trunc('month', recorded_at)::date as reporting_month,
           patient_id,
           'condition'::text as activity_type
    from core.condition_occurrence
    where recorded_at is not null
    union all
    select date_trunc('month', performed_at)::date,
           patient_id,
           'procedure'::text
    from core.procedure_occurrence
    where performed_at is not null
    union all
    select date_trunc('month', authored_at)::date,
           patient_id,
           'medication_request'::text
    from core.medication_request
    where authored_at is not null
)
select reporting_month,
       count(distinct patient_id) as patients_with_activity,
       count(*) filter (where activity_type = 'condition') as conditions,
       count(*) filter (where activity_type = 'procedure') as procedures,
       count(*) filter (where activity_type = 'medication_request') as medication_requests,
       count(*) as total_clinical_activities
from activity
group by reporting_month;
