create or replace view mart.member_eligibility_monthly as
with distinct_member_month as (
    select distinct
           month_start::date as reporting_month,
           coverage.patient_id,
           coverage.payer_organization_id
    from core.coverage coverage
    cross join lateral generate_series(
        date_trunc('month', coverage.coverage_start)::date,
        date_trunc('month', coverage.coverage_end)::date,
        interval '1 month'
    ) month_start
    where coverage.coverage_status = 'active'
      and coverage.coverage_start is not null
      and coverage.coverage_end is not null
)
select reporting_month,
       payer_organization_id,
       count(*) as member_months
from distinct_member_month
group by reporting_month, payer_organization_id;

create or replace view mart.ed_utilization_eligible_monthly as
with distinct_member_month as (
    select distinct
           month_start::date as reporting_month,
           coverage.patient_id,
           coverage.payer_organization_id
    from core.coverage coverage
    cross join lateral generate_series(
        date_trunc('month', coverage.coverage_start)::date,
        date_trunc('month', coverage.coverage_end)::date,
        interval '1 month'
    ) month_start
    where coverage.coverage_status = 'active'
      and coverage.coverage_start is not null
      and coverage.coverage_end is not null
),
eligible_ed_encounter as (
    select member.reporting_month,
           member.payer_organization_id,
           encounter.encounter_id,
           encounter.patient_id
    from distinct_member_month member
    join core.encounter encounter
      on encounter.patient_id = member.patient_id
     and date_trunc('month', encounter.start_at)::date = member.reporting_month
     and encounter.encounter_class = 'EMER'
     and encounter.encounter_status in ('finished', 'completed')
     and encounter.start_at is not null
)
select member.reporting_month,
       member.payer_organization_id,
       count(distinct member.patient_id) as member_months,
       count(encounter.encounter_id) as ed_encounters,
       count(distinct encounter.patient_id) as patients_with_ed_encounter,
       round(
           1000 * count(encounter.encounter_id)::numeric
               / nullif(count(distinct member.patient_id), 0),
           2
       ) as ed_encounters_per_1000_member_months
from distinct_member_month member
left join eligible_ed_encounter encounter
  on encounter.reporting_month = member.reporting_month
 and encounter.payer_organization_id is not distinct from member.payer_organization_id
 and encounter.patient_id = member.patient_id
group by member.reporting_month, member.payer_organization_id;
