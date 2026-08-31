-- DE-007 independent validation. Every exception query must return zero rows.

-- Entity counts for the controlled fixture in an otherwise clean claims database.
select (select count(*) from core.payer) as payers,
       (select count(distinct provider_id)
        from (
            select billing_provider_id as provider_id from core.claim
            union
            select rendering_provider_id from core.claim_line
        ) provider
        where provider_id is not null) as claim_providers,
       (select count(*) from core.claim_diagnosis) as diagnoses,
       (select count(*) from core.claim_line_procedure) as procedures,
       (select count(*) from core.claim_line_adjustment) as adjustments;

-- The replacement must resolve to its retained original.
select adjusted.claim_id, adjusted.claim_frequency_code, adjusted.original_claim_id
from core.claim adjusted
join core.claim original on original.claim_id = adjusted.original_claim_id
where adjusted.claim_id = 'c-101'
  and adjusted.claim_frequency_code = '7';

-- Header financials must equal the sum of service-line financials.
select claim.claim_id
from core.claim claim
left join core.claim_line line on line.claim_id = claim.claim_id
group by claim.claim_id, claim.billed_amount, claim.allowed_amount, claim.paid_amount,
         claim.patient_responsibility_amount, claim.adjustment_amount
having count(line.claim_line_id) = 0
    or claim.billed_amount <> sum(line.billed_amount)
    or claim.allowed_amount <> sum(line.allowed_amount)
    or claim.paid_amount <> sum(line.paid_amount)
    or claim.patient_responsibility_amount <> sum(line.patient_responsibility_amount)
    or claim.adjustment_amount <> sum(line.adjustment_amount);

-- Line adjustment totals must equal their reason-coded details.
select line.claim_line_id
from core.claim_line line
left join core.claim_line_adjustment adjustment
  on adjustment.claim_line_id = line.claim_line_id
group by line.claim_line_id, line.adjustment_amount
having line.adjustment_amount <> coalesce(sum(adjustment.adjustment_amount), 0);

-- Every replacement/void record must resolve to an original.
select adjusted.claim_id
from core.claim adjusted
left join core.claim original on original.claim_id = adjusted.original_claim_id
where adjusted.claim_frequency_code in ('7', '8')
  and original.claim_id is null;

-- Independently rebuild the current adjudication-state mart and compare it.
with current_claim as (
    select claim.claim_id
    from core.claim claim
    where claim.claim_frequency_code <> '8'
      and not exists (
          select 1 from core.claim successor
          where successor.original_claim_id = claim.claim_id
      )
), expected as (
    select date_trunc('month', line.service_date)::date as reporting_month,
           count(distinct line.claim_id) as claims,
           count(*) as claim_lines,
           sum(line.billed_amount) as billed_amount,
           sum(line.allowed_amount) as allowed_amount,
           sum(line.paid_amount) as paid_amount,
           sum(line.billed_amount - line.paid_amount) as unpaid_amount,
           sum(line.patient_responsibility_amount) as patient_responsibility_amount,
           sum(line.adjustment_amount) as adjustment_amount
    from core.claim_line line
    join current_claim on current_claim.claim_id = line.claim_id
    group by 1
), differences as (
    (select * from expected except select * from mart.claim_cost_monthly)
    union all
    (select * from mart.claim_cost_monthly except select * from expected)
)
select * from differences;
