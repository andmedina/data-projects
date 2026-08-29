create table if not exists quarantine.hl7_message (
    quarantine_id bigint generated always as identity primary key,
    run_id uuid not null references operational.pipeline_run(run_id),
    source_system text not null,
    message_control_id text,
    message_text text not null,
    reason_code text not null,
    reason_detail text,
    quarantined_at timestamptz not null default current_timestamp,
    unique (source_system, message_control_id, reason_code)
);
