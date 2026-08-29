-- Independent validation for DA-001.
-- Query 1 must return zero rows: the mart must reconcile to its core source.
with direct as (
    select date_trunc('month', start_at)::date as reporting_month,
           count(*) as ed_encounters,
           count(distinct patient_id) as patients_with_ed_encounter
    from core.encounter
    where encounter_class = 'EMER'
      and encounter_status in ('finished', 'completed')
      and start_at is not null
    group by 1
), comparison as (
    select coalesce(d.reporting_month, m.reporting_month) as reporting_month,
           d.ed_encounters as direct_ed_encounters,
           m.ed_encounters as mart_ed_encounters,
           d.patients_with_ed_encounter as direct_patients,
           m.patients_with_ed_encounter as mart_patients
    from direct d
    full outer join mart.ed_utilization_monthly m using (reporting_month)
)
select *
from comparison
where direct_ed_encounters is distinct from mart_ed_encounters
   or direct_patients is distinct from mart_patients
order by reporting_month;

-- Query 2 profiles the source mapping used by the metric.
select encounter_class, encounter_status, count(*) as encounters
from core.encounter
group by encounter_class, encounter_status
order by encounter_class, encounter_status;

-- Query 3 detects records excluded because the reporting month is unavailable.
select count(*) as emergency_encounters_missing_start_at
from core.encounter
where encounter_class = 'EMER'
  and encounter_status in ('finished', 'completed')
  and start_at is null;
