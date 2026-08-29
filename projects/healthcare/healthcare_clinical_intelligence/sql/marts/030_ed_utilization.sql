create schema if not exists mart;

create or replace view mart.ed_utilization_monthly as
select date_trunc('month', start_at)::date as reporting_month,
       count(*) as ed_encounters,
       count(distinct patient_id) as patients_with_ed_encounter,
       round(count(*)::numeric / nullif(count(distinct patient_id), 0), 2) as ed_encounters_per_patient
from core.encounter
where encounter_class = 'EMER'
  and encounter_status in ('finished', 'completed')
group by 1;
