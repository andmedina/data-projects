create or replace view mart.claim_cost_monthly as
select date_trunc('month', service_date)::date as reporting_month,
       count(distinct claim_id) as claims,
       count(*) as claim_lines,
       sum(billed_amount) as billed_amount,
       sum(allowed_amount) as allowed_amount,
       sum(paid_amount) as paid_amount,
       sum(billed_amount - paid_amount) as unpaid_amount
from core.claim_line
group by 1;
