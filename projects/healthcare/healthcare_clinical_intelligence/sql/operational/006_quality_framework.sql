create table if not exists operational.quality_check_definition (
    check_name text primary key,
    description text not null,
    quality_dimension text not null constraint quality_check_definition_dimension_check check (
        quality_dimension in ('completeness', 'validity', 'integrity', 'reconciliation', 'operability')
    ),
    severity text not null constraint quality_check_definition_severity_check check (severity in ('warning', 'error')),
    failure_threshold bigint not null default 0 check (failure_threshold >= 0),
    enabled boolean not null default true,
    updated_at timestamptz not null default current_timestamp
);

create table if not exists operational.quality_run (
    quality_run_id uuid primary key,
    pipeline_run_id uuid references operational.pipeline_run(run_id),
    triggered_by text not null,
    started_at timestamptz not null default current_timestamp,
    completed_at timestamptz,
    status text not null check (
        status in ('running', 'passed', 'passed_with_warnings', 'failed', 'error')
    ),
    fail_on_warning boolean not null default false
);

create table if not exists operational.quality_result (
    quality_run_id uuid not null references operational.quality_run(quality_run_id),
    check_name text not null references operational.quality_check_definition(check_name),
    quality_dimension text not null constraint quality_result_dimension_check check (
        quality_dimension in ('completeness', 'validity', 'integrity', 'reconciliation', 'operability')
    ),
    severity text not null constraint quality_result_severity_check check (severity in ('warning', 'error')),
    observed_value bigint,
    failure_threshold bigint not null,
    status text not null check (status in ('pass', 'warn', 'fail', 'error')),
    details jsonb not null default '{}'::jsonb,
    evaluated_at timestamptz not null default current_timestamp,
    primary key (quality_run_id, check_name)
);

create index if not exists ix_quality_run_completed_at
    on operational.quality_run (completed_at desc);

create index if not exists ix_quality_result_check_name
    on operational.quality_result (check_name, evaluated_at desc);

insert into operational.quality_check_definition
    (check_name, description, quality_dimension, severity, failure_threshold)
values
    ('orphan_observations', 'Canonical observations without a canonical patient', 'integrity', 'error', 0),
    ('invalid_encounter_periods', 'Encounters whose end timestamp precedes the start timestamp', 'validity', 'error', 0),
    ('completed_ed_encounters_missing_start', 'Completed emergency encounters without a reporting timestamp', 'completeness', 'error', 0),
    ('claim_header_line_mismatches', 'Claim headers that do not reconcile to their service lines', 'reconciliation', 'error', 0),
    ('orphan_claim_lines', 'Canonical claim lines without a canonical claim header', 'integrity', 'error', 0),
    ('quarantined_fhir_records', 'FHIR records retained in quarantine', 'validity', 'warning', 0),
    ('quarantined_claim_lines', 'Claim lines retained in quarantine', 'validity', 'warning', 0),
    ('quarantined_hl7_messages', 'HL7 messages retained in quarantine', 'validity', 'warning', 0)
on conflict (check_name) do update
set description = excluded.description,
    quality_dimension = excluded.quality_dimension,
    severity = excluded.severity,
    updated_at = current_timestamp;

-- Backfill-safe additions for environments that applied an earlier development revision.
alter table operational.quality_result
    add column if not exists quality_dimension text;

alter table operational.quality_result
    add column if not exists severity text;

update operational.quality_result r
set quality_dimension = d.quality_dimension,
    severity = d.severity
from operational.quality_check_definition d
where d.check_name = r.check_name
  and (r.quality_dimension is null or r.severity is null);

alter table operational.quality_result
    alter column quality_dimension set not null,
    alter column severity set not null;

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'quality_result_dimension_check'
          and conrelid = 'operational.quality_result'::regclass
    ) then
        alter table operational.quality_result
            add constraint quality_result_dimension_check check (
                quality_dimension in ('completeness', 'validity', 'integrity', 'reconciliation', 'operability')
            );
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'quality_result_severity_check'
          and conrelid = 'operational.quality_result'::regclass
    ) then
        alter table operational.quality_result
            add constraint quality_result_severity_check check (severity in ('warning', 'error'));
    end if;
end $$;
