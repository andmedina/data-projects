-- DA-002 independent validation. Exception queries must return zero rows.

-- Validation scope and headline totals.
select count(*) as active_coverages,
       count(distinct patient_id) as covered_patients,
       min(coverage_start) as earliest_coverage_start,
       max(coverage_end) as latest_coverage_end
from core.coverage
where coverage_status = 'active';

select count(*) as payer_month_rows,
       sum(member_months) as member_months,
       sum(ed_encounters) as eligible_ed_encounters,
       sum(patients_with_ed_encounter) as patient_months_with_ed
from mart.ed_utilization_eligible_monthly;

-- Mart denominator must equal a direct distinct expansion of active Coverage.
with expected as (
    select reporting_month,
           payer_organization_id,
           count(*) as member_months
    from (
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
    ) member_month
    group by reporting_month, payer_organization_id
)
select coalesce(expected.reporting_month, actual.reporting_month) as reporting_month,
       coalesce(expected.payer_organization_id, actual.payer_organization_id) as payer_organization_id,
       expected.member_months as expected_member_months,
       actual.member_months as actual_member_months
from expected
full join mart.member_eligibility_monthly actual
  on actual.reporting_month = expected.reporting_month
 and actual.payer_organization_id is not distinct from expected.payer_organization_id
where expected.member_months is distinct from actual.member_months;

-- Numerator must equal qualified ED encounters joined to an eligible member month.
with member_month as (
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
expected as (
    select member_month.reporting_month,
           member_month.payer_organization_id,
           count(encounter.encounter_id) as ed_encounters,
           count(distinct encounter.patient_id) as patients_with_ed_encounter
    from member_month
    left join core.encounter encounter
      on encounter.patient_id = member_month.patient_id
     and date_trunc('month', encounter.start_at)::date = member_month.reporting_month
     and encounter.encounter_class = 'EMER'
     and encounter.encounter_status in ('finished', 'completed')
     and encounter.start_at is not null
    group by member_month.reporting_month, member_month.payer_organization_id
)
select actual.reporting_month,
       actual.payer_organization_id,
       expected.ed_encounters as expected_ed_encounters,
       actual.ed_encounters as actual_ed_encounters,
       expected.patients_with_ed_encounter as expected_patients,
       actual.patients_with_ed_encounter as actual_patients
from mart.ed_utilization_eligible_monthly actual
join expected
  on expected.reporting_month = actual.reporting_month
 and expected.payer_organization_id is not distinct from actual.payer_organization_id
where expected.ed_encounters is distinct from actual.ed_encounters
   or expected.patients_with_ed_encounter is distinct from actual.patients_with_ed_encounter;

-- Published rate must use the documented denominator and scale.
select reporting_month,
       payer_organization_id,
       member_months,
       ed_encounters,
       ed_encounters_per_1000_member_months
from mart.ed_utilization_eligible_monthly
where ed_encounters_per_1000_member_months is distinct from
      round(1000 * ed_encounters::numeric / nullif(member_months, 0), 2);

-- Blocking Coverage-period exceptions must be absent.
select coverage_id, patient_id, coverage_start, coverage_end
from core.coverage
where coverage_status = 'active'
  and (coverage_start is null or coverage_end is null);

select first_coverage.coverage_id as first_coverage_id,
       second_coverage.coverage_id as second_coverage_id,
       first_coverage.patient_id,
       first_coverage.payer_organization_id
from core.coverage first_coverage
join core.coverage second_coverage
  on second_coverage.patient_id = first_coverage.patient_id
 and second_coverage.payer_organization_id is not distinct from first_coverage.payer_organization_id
 and second_coverage.coverage_id > first_coverage.coverage_id
 and second_coverage.coverage_status = 'active'
 and second_coverage.coverage_start <= first_coverage.coverage_end
 and first_coverage.coverage_start <= second_coverage.coverage_end
where first_coverage.coverage_status = 'active';
