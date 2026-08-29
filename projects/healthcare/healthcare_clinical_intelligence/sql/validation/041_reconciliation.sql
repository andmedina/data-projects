-- Run-level raw ingestion reconciliation. Each row should balance.
select r.run_id,
       coalesce(f.raw_loaded, 0) as raw_loaded,
       coalesce(q.quarantined, 0) as quarantined,
       coalesce(f.raw_loaded, 0) + coalesce(q.quarantined, 0) as accounted_records
from operational.pipeline_run r
left join (
    select run_id, count(*) as raw_loaded
    from raw.fhir_resource
    group by run_id
) f on f.run_id = r.run_id
left join (
    select run_id, count(*) as quarantined
    from quarantine.fhir_resource
    group by run_id
) q on q.run_id = r.run_id
where r.pipeline_name = 'fhir_raw_ingestion'
