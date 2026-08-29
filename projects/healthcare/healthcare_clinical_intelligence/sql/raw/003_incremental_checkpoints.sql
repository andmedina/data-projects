create table if not exists operational.ingestion_checkpoint (
    pipeline_name text not null,
    source_system text not null,
    resource_type text not null,
    watermark_at timestamptz not null,
    last_successful_run_id uuid references operational.pipeline_run(run_id),
    updated_at timestamptz not null default current_timestamp,
    primary key (pipeline_name, source_system, resource_type)
);
