create or replace view mart.claim_cost_monthly as
with current_claim as (
    select claim.claim_id
    from core.claim claim
    where claim.claim_frequency_code <> '8'
      and not exists (
          select 1
          from core.claim successor
          where successor.original_claim_id = claim.claim_id
      )
)
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
group by 1;
