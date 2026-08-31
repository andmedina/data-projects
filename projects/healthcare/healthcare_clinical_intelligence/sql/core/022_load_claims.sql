-- Controlled claim dimensions are loaded before facts so all foreign keys resolve.
insert into core.payer (payer_id, payer_name, source_system)
select payer_id, max(payer_name), max(source_system)
from staging.stg_claim_line
where payer_id is not null
group by payer_id
on conflict (payer_id) do update
set payer_name = coalesce(excluded.payer_name, core.payer.payer_name),
    source_system = excluded.source_system;

insert into core.provider (provider_id, provider_name, npi, source_system)
select provider_id, max(provider_name), max(npi), max(source_system)
from (
    select billing_provider_id as provider_id,
           billing_provider_name as provider_name,
           billing_provider_npi as npi,
           source_system
    from staging.stg_claim_line
    union all
    select rendering_provider_id,
           rendering_provider_name,
           rendering_provider_npi,
           source_system
    from staging.stg_claim_line
) claim_provider
where provider_id is not null
group by provider_id
on conflict (provider_id) do update
set provider_name = coalesce(excluded.provider_name, core.provider.provider_name),
    npi = coalesce(excluded.npi, core.provider.npi),
    source_system = excluded.source_system;

-- Claim header values are the sum of their latest service-line versions.
insert into core.claim (
    claim_id,
    patient_id,
    service_date,
    payer_id,
    billing_provider_id,
    claim_frequency_code,
    original_claim_id,
    billed_amount,
    allowed_amount,
    paid_amount,
    patient_responsibility_amount,
    adjustment_amount
)
select claim_id,
       max(patient_id),
       min(service_date),
       max(payer_id),
       max(billing_provider_id),
       max(claim_frequency_code),
       max(original_claim_id),
       sum(billed_amount),
       sum(allowed_amount),
       sum(paid_amount),
       sum(patient_responsibility_amount),
       sum(adjustment_amount)
from staging.stg_claim_line
where patient_id in (select patient_id from core.patient)
group by claim_id
on conflict (claim_id) do update
set patient_id = excluded.patient_id,
    service_date = excluded.service_date,
    payer_id = excluded.payer_id,
    billing_provider_id = excluded.billing_provider_id,
    claim_frequency_code = excluded.claim_frequency_code,
    original_claim_id = excluded.original_claim_id,
    billed_amount = excluded.billed_amount,
    allowed_amount = excluded.allowed_amount,
    paid_amount = excluded.paid_amount,
    patient_responsibility_amount = excluded.patient_responsibility_amount,
    adjustment_amount = excluded.adjustment_amount;

insert into core.claim_line (
    claim_line_id,
    claim_id,
    patient_id,
    service_date,
    rendering_provider_id,
    billed_amount,
    allowed_amount,
    paid_amount,
    patient_responsibility_amount,
    adjustment_amount
)
select claim_line_id,
       claim_id,
       patient_id,
       service_date,
       rendering_provider_id,
       billed_amount,
       allowed_amount,
       paid_amount,
       patient_responsibility_amount,
       adjustment_amount
from staging.stg_claim_line
where patient_id in (select patient_id from core.patient)
on conflict (claim_line_id) do update
set claim_id = excluded.claim_id,
    patient_id = excluded.patient_id,
    service_date = excluded.service_date,
    rendering_provider_id = excluded.rendering_provider_id,
    billed_amount = excluded.billed_amount,
    allowed_amount = excluded.allowed_amount,
    paid_amount = excluded.paid_amount,
    patient_responsibility_amount = excluded.patient_responsibility_amount,
    adjustment_amount = excluded.adjustment_amount;

-- Replace repeating code/adjustment children for every claim represented in staging.
delete from core.claim_diagnosis diagnosis
using (select distinct claim_id from staging.stg_claim_line) current_claim
where diagnosis.claim_id = current_claim.claim_id;

with claim_diagnosis_source as (
    select distinct on (claim_id) claim_id, diagnosis_codes
    from staging.stg_claim_line
    where nullif(diagnosis_codes, '') is not null
    order by claim_id, raw_claim_line_id desc
)
insert into core.claim_diagnosis (claim_id, diagnosis_sequence, code_system, code)
select source.claim_id,
       diagnosis.ordinality::integer,
       split_part(diagnosis.token, ':', 1),
       substring(diagnosis.token from position(':' in diagnosis.token) + 1)
from claim_diagnosis_source source
cross join lateral regexp_split_to_table(source.diagnosis_codes, '\|')
    with ordinality as diagnosis(token, ordinality)
on conflict (claim_id, diagnosis_sequence) do update
set code_system = excluded.code_system,
    code = excluded.code;

delete from core.claim_line_procedure procedure_code
using staging.stg_claim_line current_line
where procedure_code.claim_line_id = current_line.claim_line_id;

insert into core.claim_line_procedure (claim_line_id, code_system, code)
select claim_line_id, procedure_code_system, procedure_code
from staging.stg_claim_line
where procedure_code_system is not null and procedure_code is not null
on conflict (claim_line_id, code_system, code) do nothing;

delete from core.claim_line_adjustment adjustment
using staging.stg_claim_line current_line
where adjustment.claim_line_id = current_line.claim_line_id;

insert into core.claim_line_adjustment (
    claim_line_id,
    adjustment_group_code,
    adjustment_reason_code,
    adjustment_amount
)
select claim_line_id,
       adjustment_group_code,
       adjustment_reason_code,
       adjustment_amount
from staging.stg_claim_line
where adjustment_amount > 0
on conflict (claim_line_id, adjustment_group_code, adjustment_reason_code) do update
set adjustment_amount = excluded.adjustment_amount;
