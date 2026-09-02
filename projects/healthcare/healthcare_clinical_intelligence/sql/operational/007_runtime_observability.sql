-- Backward-compatible runtime metadata, migration history, and operational health views.

create table if not exists operational.schema_migration (
    migration_name text primary key,
    checksum_sha256 text not null,
    applied_at timestamptz not null default current_timestamp,
    execution_ms numeric(14, 3) not null default 0,
    application_count integer not null default 1 check (application_count > 0)
);

alter table operational.pipeline_run add column if not exists records_seen bigint;
alter table operational.pipeline_run add column if not exists records_loaded bigint;
alter table operational.pipeline_run add column if not exists records_rejected bigint;
alter table operational.pipeline_run add column if not exists records_duplicates bigint;
alter table operational.pipeline_run add column if not exists details jsonb not null default '{}'::jsonb;
alter table operational.pipeline_run add column if not exists updated_at timestamptz not null default current_timestamp;

create index if not exists ix_pipeline_run_status_started_at
    on operational.pipeline_run (status, started_at desc);

create index if not exists ix_pipeline_run_name_started_at
    on operational.pipeline_run (pipeline_name, started_at desc);

create index if not exists ix_raw_fhir_resource_run_id
    on raw.fhir_resource (run_id);

create index if not exists ix_raw_claim_line_run_id
    on raw.claim_line (run_id);

create index if not exists ix_raw_hl7_message_run_id
    on raw.hl7_message (run_id);

create index if not exists ix_encounter_patient_start_at
    on core.encounter (patient_id, start_at desc);

create index if not exists ix_observation_patient_effective_at
    on core.observation (patient_id, effective_at desc);

create index if not exists ix_condition_patient_recorded_at
    on core.condition_occurrence (patient_id, recorded_at desc);

create index if not exists ix_procedure_patient_performed_at
    on core.procedure_occurrence (patient_id, performed_at desc);

create index if not exists ix_medication_patient_authored_at
    on core.medication_request (patient_id, authored_at desc);

create or replace view operational.pipeline_run_health as
select
    run_id,
    pipeline_name,
    source_description,
    status,
    started_at,
    completed_at,
    updated_at,
    records_seen,
    records_loaded,
    records_duplicates,
    records_rejected,
    details,
    case
        when completed_at is not null then extract(epoch from completed_at - started_at)
        else extract(epoch from current_timestamp - started_at)
    end as duration_seconds,
    status = 'running' and started_at < current_timestamp - interval '2 hours' as is_stale,
    status <> 'running' and completed_at is null as terminal_state_missing_completion,
    records_seen is not null
        and records_seen <> coalesce(records_loaded, 0) + coalesce(records_duplicates, 0) + coalesce(records_rejected, 0)
        as has_count_mismatch
from operational.pipeline_run;
