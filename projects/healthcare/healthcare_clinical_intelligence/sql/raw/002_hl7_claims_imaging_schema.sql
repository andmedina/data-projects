create table if not exists raw.hl7_message (
    raw_hl7_message_id bigint generated always as identity primary key,
    source_system text not null,
    message_control_id text,
    message_type text,
    message_text text not null,
    payload_sha256 text not null unique,
    run_id uuid references operational.pipeline_run(run_id),
    ingested_at timestamptz not null default current_timestamp
);

create table if not exists raw.claim_line (
    raw_claim_line_id bigint generated always as identity primary key,
    source_system text not null,
    source_claim_id text not null,
    source_claim_line_id text not null,
    payload jsonb not null,
    payload_sha256 text not null,
    run_id uuid references operational.pipeline_run(run_id),
    unique (source_system, source_claim_line_id, payload_sha256)
);

create table if not exists raw.imaging_study (
    raw_imaging_study_id bigint generated always as identity primary key,
    source_system text not null,
    source_study_id text not null,
    metadata jsonb not null,
    run_id uuid references operational.pipeline_run(run_id),
    unique (source_system, source_study_id)
);
