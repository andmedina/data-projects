create table if not exists quarantine.claim_line (
    quarantine_id bigint generated always as identity primary key,
    run_id uuid not null references operational.pipeline_run(run_id),
    source_system text not null,
    source_claim_id text,
    source_claim_line_id text,
    payload jsonb not null,
    reason_code text not null,
    reason_detail text,
    quarantined_at timestamptz not null default current_timestamp,
    unique (source_system, source_claim_line_id, reason_code)
);
