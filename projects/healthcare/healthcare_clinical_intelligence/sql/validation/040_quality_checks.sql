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
group by c.claim_id, c.billed_amount, c.allowed_amount, c.paid_amount,
         c.patient_responsibility_amount, c.adjustment_amount
having c.billed_amount <> sum(l.billed_amount)
    or c.allowed_amount <> sum(l.allowed_amount)
    or c.paid_amount <> sum(l.paid_amount)
    or c.patient_responsibility_amount <> sum(l.patient_responsibility_amount)
    or c.adjustment_amount <> sum(l.adjustment_amount);

-- Replacement/void claims must resolve to an original claim retained in core.
select adjusted.claim_id
from core.claim adjusted
left join core.claim original on original.claim_id = adjusted.original_claim_id
where adjusted.claim_frequency_code in ('7', '8')
  and original.claim_id is null;

-- Line-level adjustment summaries must reconcile to normalized adjustment details.
select cl.claim_line_id
from core.claim_line cl
left join core.claim_line_adjustment adjustment
  on adjustment.claim_line_id = cl.claim_line_id
group by cl.claim_line_id, cl.adjustment_amount
having cl.adjustment_amount <> coalesce(sum(adjustment.adjustment_amount), 0);

-- Header attributes repeated by the CSV line grain must agree within a claim.
select claim_id
from staging.stg_claim_line
group by claim_id
having count(distinct patient_id) > 1
    or count(distinct coalesce(payer_id, '')) > 1
    or count(distinct coalesce(billing_provider_id, '')) > 1
    or count(distinct claim_frequency_code) > 1
    or count(distinct coalesce(original_claim_id, '')) > 1
    or count(distinct coalesce(diagnosis_codes, '')) > 1;
