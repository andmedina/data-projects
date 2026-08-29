-- Phase 1 raw landing and operational metadata schema.
-- Raw payloads are retained for replay, audit, and transformation debugging.

create schema if not exists operational;
create schema if not exists raw;
create schema if not exists quarantine;

create table if not exists operational.pipeline_run (
    run_id uuid primary key,
    pipeline_name text not null,
    started_at timestamptz not null default current_timestamp,
    completed_at timestamptz,
    status text not null check (status in ('running', 'succeeded', 'failed', 'partial')),
    source_description text not null,
    created_at timestamptz not null default current_timestamp
);

create table if not exists raw.fhir_resource (
    raw_resource_id bigint generated always as identity primary key,
    source_system text not null,
    resource_type text not null,
    source_resource_id text not null,
    last_updated_at timestamptz,
    payload jsonb not null,
    payload_sha256 text not null,
    ingested_at timestamptz not null default current_timestamp,
    run_id uuid not null references operational.pipeline_run(run_id),
    unique (source_system, resource_type, source_resource_id, payload_sha256)
);

create index if not exists ix_raw_fhir_resource_type_id
    on raw.fhir_resource (resource_type, source_resource_id);

create table if not exists quarantine.fhir_resource (
    quarantine_id bigint generated always as identity primary key,
    run_id uuid not null references operational.pipeline_run(run_id),
    source_system text not null,
    resource_type text,
    source_resource_id text,
    payload jsonb,
    reason_code text not null,
    reason_detail text,
    quarantined_at timestamptz not null default current_timestamp,
    unique (source_system, resource_type, source_resource_id, reason_code)
);
