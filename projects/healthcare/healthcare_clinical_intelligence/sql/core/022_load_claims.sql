-- Claim header values are the sum of their service lines in this controlled CSV model.
insert into core.claim (claim_id, patient_id, service_date, billed_amount, allowed_amount, paid_amount)
select claim_id, max(patient_id), min(service_date), sum(billed_amount), sum(allowed_amount), sum(paid_amount)
from staging.stg_claim_line
where patient_id in (select patient_id from core.patient)
group by claim_id
on conflict (claim_id) do update
set patient_id = excluded.patient_id, service_date = excluded.service_date,
    billed_amount = excluded.billed_amount, allowed_amount = excluded.allowed_amount, paid_amount = excluded.paid_amount;

insert into core.claim_line (claim_line_id, claim_id, patient_id, service_date, billed_amount, allowed_amount, paid_amount)
select claim_line_id, claim_id, patient_id, service_date, billed_amount, allowed_amount, paid_amount
from staging.stg_claim_line
where patient_id in (select patient_id from core.patient)
on conflict (claim_line_id) do update
set claim_id = excluded.claim_id, patient_id = excluded.patient_id, service_date = excluded.service_date,
    billed_amount = excluded.billed_amount, allowed_amount = excluded.allowed_amount, paid_amount = excluded.paid_amount;
