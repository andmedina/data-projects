-- The latest completed run must evaluate every enabled definition.
with latest as (
    select quality_run_id, status
    from operational.quality_run
    where completed_at is not null
    order by completed_at desc
    limit 1
)
select l.quality_run_id,
       l.status,
       (select count(*) from operational.quality_check_definition where enabled) as enabled_checks,
       count(r.check_name) as persisted_results
from latest l
left join operational.quality_result r using (quality_run_id)
group by l.quality_run_id, l.status;

-- Must return zero rows for a healthy non-strict run.
with latest as (
    select quality_run_id
    from operational.quality_run
    where completed_at is not null
    order by completed_at desc
    limit 1
)
select r.check_name, r.severity, r.observed_value, r.failure_threshold, r.status
from operational.quality_result r
join latest l using (quality_run_id)
where r.status in ('fail', 'error');

-- Demonstrates durable normal and strict-mode histories.
select triggered_by, fail_on_warning, status, count(*) as runs
from operational.quality_run
group by triggered_by, fail_on_warning, status
order by triggered_by, fail_on_warning, status;

-- Must return zero rows: completed runs cannot remain in a running state.
select quality_run_id
from operational.quality_run
where status = 'running'
  and started_at < current_timestamp - interval '15 minutes';
