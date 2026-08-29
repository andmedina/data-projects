-- Queries should return zero rows to pass.
select patient_id from core.patient group by 1 having count(*) > 1;

select encounter_id
from core.encounter
where end_at < start_at;

select o.observation_id
from core.observation o
left join core.patient p using (patient_id)
where p.patient_id is null;

-- Reconciliation: raw = valid core records + quarantined records, by resource type
select resource_type, count(*) as raw_count
from raw.fhir_resource
group by 1;

-- Claim headers must reconcile exactly to their loaded service lines.
select c.claim_id
from core.claim c
join core.claim_line l on l.claim_id = c.claim_id
group by c.claim_id, c.billed_amount, c.allowed_amount, c.paid_amount
having c.billed_amount <> sum(l.billed_amount)
    or c.allowed_amount <> sum(l.allowed_amount)
    or c.paid_amount <> sum(l.paid_amount);
