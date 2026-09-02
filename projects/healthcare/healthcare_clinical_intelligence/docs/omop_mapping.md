# OMOP-Compatible Analytical Subset

## Scope and status

The `omop` schema exposes source-preserving views shaped to selected OMOP CDM v5.4 tables. It follows the published [OMOP CDM v5.4 field specification](https://ohdsi.github.io/CommonDataModel/cdm54.html) and compares column shapes with the [official PostgreSQL v5.4 DDL](https://github.com/OHDSI/CommonDataModel/blob/v5.4.0/inst/ddl/5.4/postgresql/OMOPCDM_postgresql_5.4_ddl.sql).

This is not an OMOP-conformant CDM instance. It does not instantiate the full CDM, load an Athena vocabulary release, pass the OHDSI Data Quality Dashboard, or run Achilles. It is an auditable intermediate extract that makes those remaining dependencies visible.

## Implemented mappings

| OMOP-compatible view | Canonical source | Inclusion rule | Standard concept handling |
| --- | --- | --- | --- |
| `omop.person` | `core.patient` | birth date is present | source administrative gender retained; concept IDs are `0` pending governed semantic/vocabulary mapping |
| `omop.observation_period` | active `core.coverage`; clinical-event fallback | merge overlapping/adjacent Coverage periods; use earliest-to-latest clinical event only when Coverage is absent | period type concept ID is `0` |
| `omop.visit_occurrence` | `core.encounter` | start timestamp is present | controlled FHIR classes map `IMP`→9201, `AMB`→9202, and `EMER`→9203; type/source concept IDs remain `0` |
| `omop.condition_occurrence` | `core.condition_occurrence` | recorded timestamp is present | source system/code/status retained; concept IDs are `0` |
| `omop.procedure_occurrence` | `core.procedure_occurrence` | performed timestamp is present | source system/code retained; concept IDs are `0` |
| `omop.measurement` | laboratory `core.observation` | effective timestamp is present | source code, typed numeric value, and source unit retained; concept IDs are `0` |
| `omop.drug_exposure` | `core.medication_request` | authored timestamp is present | source RxNorm-like code retained; concept IDs are `0`; start=end is an order-date proxy, not evidence of dispensing or administration |
| `omop.payer_plan_period` | active `core.coverage` | complete ordered period is present | payer organization source value retained; concept IDs are `0` |

OMOP-required concept columns use concept ID `0` when the project cannot defend a Standard Concept mapping. The only controlled Standard Concept mapping in this release is the three encounter-class-to-Visit concepts listed above. `omop.source_to_standard_concept_status` inventories every distinct source code, row count, target concept, and mapped/unmapped status.

## Identifiers and lineage

`omop.entity_id_map` assigns one stable PostgreSQL integer to each entity type/source ID. Inserts are ordered and use `ON CONFLICT DO NOTHING`, so reruns preserve existing IDs and add only newly qualified records. The bridge remains the direct link back to canonical source identifiers; OMOP source-value fields retain clinical source codes rather than overloading them with record IDs.

`omop-refresh` populates new identifiers after a core load. The standard FHIR/core command and Airflow core-load task run the same refresh automatically.

## Observation-period policy

Active Coverage is the preferred evidence of data observability. Periods are merged across payers when they overlap or are adjacent because OMOP observation periods for one person cannot overlap or be back-to-back. A patient without Coverage receives one fallback period from their earliest through latest canonical encounter, observation, condition, procedure, or medication-request date. The helper view retains `period_provenance` so this assumption is inspectable.

Events may occur outside an observation period, but absence of events outside those periods must never be interpreted as absence of disease or care. Cohort use requires a separate minimum-observation policy.

## Remaining work for conformance

- Load a licensed/governed Athena vocabulary release and create source-to-standard mappings for demographics, LOINC, ICD-10-CM, CPT, RxNorm, UCUM, type, and payer concepts.
- Replace the MedicationRequest order-date proxy with dispense, administration, or claims evidence before research use.
- Add every required CDM v5.4 table, keys/indexes, CDM source metadata, and vocabulary tables.
- Validate person demographic semantics, visit derivation, event dates, provenance concepts, and observation-period policy with accountable domain owners.
- Run the OHDSI Data Quality Dashboard and Achilles, triage all findings, and version the results.

Until those steps are complete, dashboards must label these objects “OMOP-compatible extract views,” never “OMOP-conformant data.”
