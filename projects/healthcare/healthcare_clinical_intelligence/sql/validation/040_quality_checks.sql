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
