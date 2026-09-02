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
    category_system text,
    category_code text,
    effective_at timestamptz,
    value_type text constraint observation_value_type_check check (
        value_type is null or value_type in ('Quantity', 'String', 'Boolean', 'Integer', 'CodeableConcept')
    ),
    value_numeric numeric,
    value_text text,
    value_boolean boolean,
    value_code_system text,
    value_code text,
    value_code_display text,
    unit text,
    unit_system text,
    unit_code text,
    data_absent_reason_code text,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

-- Backfill-safe additions for existing development databases.
alter table core.observation add column if not exists category_system text;
alter table core.observation add column if not exists category_code text;
alter table core.observation add column if not exists value_type text;
alter table core.observation add column if not exists value_numeric numeric;
alter table core.observation add column if not exists value_text text;
alter table core.observation add column if not exists value_boolean boolean;
alter table core.observation add column if not exists value_code_system text;
alter table core.observation add column if not exists value_code text;
alter table core.observation add column if not exists value_code_display text;
alter table core.observation add column if not exists unit text;
alter table core.observation add column if not exists unit_system text;
alter table core.observation add column if not exists unit_code text;
alter table core.observation add column if not exists data_absent_reason_code text;

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'observation_value_type_check'
          and conrelid = 'core.observation'::regclass
    ) then
        alter table core.observation
            add constraint observation_value_type_check check (
                value_type is null or value_type in ('Quantity', 'String', 'Boolean', 'Integer', 'CodeableConcept')
            );
    end if;
end $$;

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
    npi text,
    source_system text,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

alter table core.provider add column if not exists npi text;
alter table core.provider add column if not exists source_system text;

create table if not exists core.payer (
    payer_id text primary key,
    payer_name text,
    source_system text
);

create table if not exists core.coverage (
    coverage_id text primary key,
    patient_id text not null references core.patient(patient_id),
    payer_organization_id text references core.organization(organization_id),
    coverage_status text,
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id),
    coverage_start date,
    coverage_end date,
    constraint coverage_period_check check (
        coverage_end is null or coverage_start is null or coverage_end >= coverage_start
    )
);

alter table core.coverage add column if not exists coverage_start date;
alter table core.coverage add column if not exists coverage_end date;

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'coverage_period_check'
          and conrelid = 'core.coverage'::regclass
    ) then
        alter table core.coverage
            add constraint coverage_period_check check (
                coverage_end is null or coverage_start is null or coverage_end >= coverage_start
            );
    end if;
end $$;

create index if not exists ix_coverage_member_period
    on core.coverage (patient_id, payer_organization_id, coverage_start, coverage_end)
    where coverage_status = 'active';

create table if not exists core.imaging_study (
    imaging_study_id text primary key,
    patient_id text not null references core.patient(patient_id),
    encounter_id text references core.encounter(encounter_id),
    study_status text not null,
    started_at timestamptz not null,
    study_uid text,
    accession_identifier text,
    number_of_series integer check (number_of_series is null or number_of_series >= 0),
    number_of_instances integer check (number_of_instances is null or number_of_instances >= 0),
    source_raw_resource_id bigint unique references raw.fhir_resource(raw_resource_id)
);

create table if not exists core.imaging_series (
    imaging_study_id text not null references core.imaging_study(imaging_study_id),
    series_uid text not null,
    series_number integer,
    modality_system text,
    modality_code text not null,
    body_site_system text,
    body_site_code text,
    number_of_instances integer check (number_of_instances is null or number_of_instances >= 0),
    primary key (imaging_study_id, series_uid)
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

create table if not exists core.claim (
    claim_id text primary key,
    patient_id text not null references core.patient(patient_id),
    service_date date not null,
    payer_id text references core.payer(payer_id),
    billing_provider_id text references core.provider(provider_id),
    claim_frequency_code text not null default '1' constraint claim_frequency_code_check check (claim_frequency_code in ('1', '7', '8')),
    original_claim_id text,
    billed_amount numeric(14, 2) not null check (billed_amount >= 0),
    allowed_amount numeric(14, 2) not null check (allowed_amount >= 0),
    paid_amount numeric(14, 2) not null check (paid_amount >= 0),
    patient_responsibility_amount numeric(14, 2) not null default 0 constraint claim_patient_responsibility_nonnegative_check check (patient_responsibility_amount >= 0),
    adjustment_amount numeric(14, 2) not null default 0 constraint claim_adjustment_nonnegative_check check (adjustment_amount >= 0),
    check (paid_amount <= allowed_amount and allowed_amount <= billed_amount)
);

alter table core.claim add column if not exists payer_id text references core.payer(payer_id);
alter table core.claim add column if not exists billing_provider_id text references core.provider(provider_id);
alter table core.claim add column if not exists claim_frequency_code text not null default '1';
alter table core.claim add column if not exists original_claim_id text;
alter table core.claim add column if not exists patient_responsibility_amount numeric(14, 2) not null default 0;
alter table core.claim add column if not exists adjustment_amount numeric(14, 2) not null default 0;

create table if not exists core.claim_line (
    claim_line_id text primary key,
    claim_id text not null references core.claim(claim_id),
    patient_id text not null references core.patient(patient_id),
    service_date date not null,
    rendering_provider_id text references core.provider(provider_id),
    billed_amount numeric(14, 2) not null check (billed_amount >= 0),
    allowed_amount numeric(14, 2) not null check (allowed_amount >= 0),
    paid_amount numeric(14, 2) not null check (paid_amount >= 0),
    patient_responsibility_amount numeric(14, 2) not null default 0 constraint claim_line_patient_responsibility_nonnegative_check check (patient_responsibility_amount >= 0),
    adjustment_amount numeric(14, 2) not null default 0 constraint claim_line_adjustment_nonnegative_check check (adjustment_amount >= 0),
    check (paid_amount <= allowed_amount and allowed_amount <= billed_amount)
);

alter table core.claim_line add column if not exists rendering_provider_id text references core.provider(provider_id);
alter table core.claim_line add column if not exists patient_responsibility_amount numeric(14, 2) not null default 0;
alter table core.claim_line add column if not exists adjustment_amount numeric(14, 2) not null default 0;

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'claim_frequency_code_check'
          and conrelid = 'core.claim'::regclass
    ) then
        alter table core.claim
            add constraint claim_frequency_code_check check (claim_frequency_code in ('1', '7', '8'));
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'claim_patient_responsibility_nonnegative_check'
          and conrelid = 'core.claim'::regclass
    ) then
        alter table core.claim
            add constraint claim_patient_responsibility_nonnegative_check check (patient_responsibility_amount >= 0);
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'claim_adjustment_nonnegative_check'
          and conrelid = 'core.claim'::regclass
    ) then
        alter table core.claim
            add constraint claim_adjustment_nonnegative_check check (adjustment_amount >= 0);
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'claim_line_patient_responsibility_nonnegative_check'
          and conrelid = 'core.claim_line'::regclass
    ) then
        alter table core.claim_line
            add constraint claim_line_patient_responsibility_nonnegative_check check (patient_responsibility_amount >= 0);
    end if;
    if not exists (
        select 1 from pg_constraint
        where conname = 'claim_line_adjustment_nonnegative_check'
          and conrelid = 'core.claim_line'::regclass
    ) then
        alter table core.claim_line
            add constraint claim_line_adjustment_nonnegative_check check (adjustment_amount >= 0);
    end if;
end $$;

create table if not exists core.claim_diagnosis (
    claim_id text not null references core.claim(claim_id),
    diagnosis_sequence integer not null check (diagnosis_sequence > 0),
    code_system text not null,
    code text not null,
    primary key (claim_id, diagnosis_sequence)
);

create table if not exists core.claim_line_procedure (
    claim_line_id text not null references core.claim_line(claim_line_id),
    code_system text not null,
    code text not null,
    primary key (claim_line_id, code_system, code)
);

create table if not exists core.claim_line_adjustment (
    claim_line_id text not null references core.claim_line(claim_line_id),
    adjustment_group_code text not null,
    adjustment_reason_code text not null,
    adjustment_amount numeric(14, 2) not null check (adjustment_amount > 0),
    primary key (claim_line_id, adjustment_group_code, adjustment_reason_code)
);

create index if not exists ix_claim_payer_id on core.claim (payer_id);
create index if not exists ix_claim_billing_provider_id on core.claim (billing_provider_id);
create index if not exists ix_claim_original_claim_id on core.claim (original_claim_id);
create index if not exists ix_claim_line_rendering_provider_id on core.claim_line (rendering_provider_id);

create table if not exists core.hl7_observation (
    hl7_observation_id bigint generated always as identity primary key,
    patient_id text not null references core.patient(patient_id),
    message_control_id text not null,
    obx_set_id text not null,
    value_type text,
    code text,
    value text,
    units text,
    result_status text,
    source_raw_hl7_message_id bigint not null references raw.hl7_message(raw_hl7_message_id),
    unique (message_control_id, obx_set_id)
);

create table if not exists core.hl7_encounter_event (
    hl7_encounter_event_id bigint generated always as identity primary key,
    patient_id text not null references core.patient(patient_id),
    encounter_id text not null,
    message_control_id text not null unique,
    event_code text not null constraint hl7_encounter_event_code_check check (event_code in ('A01', 'A02', 'A03', 'A08')),
    event_state text not null constraint hl7_encounter_event_state_check check (event_state in ('admitted', 'transferred', 'discharged', 'updated')),
    patient_class text,
    assigned_location text,
    prior_location text,
    event_at timestamptz not null,
    source_raw_hl7_message_id bigint not null unique references raw.hl7_message(raw_hl7_message_id)
);

create table if not exists core.hl7_order_event (
    hl7_order_event_id bigint generated always as identity primary key,
    order_id text not null,
    patient_id text not null references core.patient(patient_id),
    encounter_id text,
    message_control_id text not null,
    order_control text not null constraint hl7_order_control_check check (order_control in ('NW', 'CA', 'DC', 'XO', 'SC')),
    order_status text,
    code_system text,
    code text not null,
    code_display text,
    ordered_at timestamptz not null,
    event_at timestamptz not null,
    source_raw_hl7_message_id bigint not null references raw.hl7_message(raw_hl7_message_id),
    unique (message_control_id, order_id)
);

alter table core.hl7_order_event add column if not exists event_at timestamptz;
update core.hl7_order_event set event_at = ordered_at where event_at is null;
alter table core.hl7_order_event alter column event_at set not null;

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'hl7_order_control_check'
          and conrelid = 'core.hl7_order_event'::regclass
    ) then
        alter table core.hl7_order_event
            add constraint hl7_order_control_check check (order_control in ('NW', 'CA', 'DC', 'XO', 'SC'));
    end if;
end $$;

create index if not exists ix_hl7_encounter_event_timeline
    on core.hl7_encounter_event (encounter_id, event_at);

create index if not exists ix_hl7_order_event_event_timeline
    on core.hl7_order_event (order_id, event_at);
