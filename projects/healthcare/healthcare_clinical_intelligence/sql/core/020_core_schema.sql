create schema if not exists core;

create table if not exists core.patient (
    patient_id text primary key,
    birth_date date,
    sex text,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

create table if not exists core.encounter (
    encounter_id text primary key,
    patient_id text not null references core.patient(patient_id),
    encounter_status text not null,
    encounter_class text,
    start_at timestamptz,
    end_at timestamptz,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id),
    check (end_at is null or start_at is null or end_at >= start_at)
);

create table if not exists core.observation (
    observation_id text primary key,
    patient_id text not null references core.patient(patient_id),
    encounter_id text references core.encounter(encounter_id),
    observation_status text not null,
    coding_system text,
    code text,
    effective_at timestamptz,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

create table if not exists core.organization (
    organization_id text primary key,
    organization_name text,
    organization_type_system text,
    organization_type_code text,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

create table if not exists core.provider (
    provider_id text primary key,
    provider_name text,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

create table if not exists core.coverage (
    coverage_id text primary key,
    patient_id text not null references core.patient(patient_id),
    payer_organization_id text references core.organization(organization_id),
    coverage_status text,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

create table if not exists core.condition_occurrence (
    condition_id text primary key,
    patient_id text not null references core.patient(patient_id),
    encounter_id text references core.encounter(encounter_id),
    clinical_status text,
    coding_system text,
    code text,
    recorded_at timestamptz,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

create table if not exists core.procedure_occurrence (
    procedure_id text primary key,
    patient_id text not null references core.patient(patient_id),
    encounter_id text references core.encounter(encounter_id),
    procedure_status text,
    coding_system text,
    code text,
    performed_at timestamptz,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

create table if not exists core.medication_request (
    medication_request_id text primary key,
    patient_id text not null references core.patient(patient_id),
    encounter_id text references core.encounter(encounter_id),
    medication_status text,
    coding_system text,
    code text,
    authored_at timestamptz,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);
