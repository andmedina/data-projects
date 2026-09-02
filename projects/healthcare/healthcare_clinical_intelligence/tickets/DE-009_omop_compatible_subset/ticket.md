# DE-009 — Build a Source-Preserving OMOP-Compatible Subset

## Business context

The canonical FHIR model has trustworthy lineage, but research consumers often expect OMOP CDM table shapes and integer keys. The project needs a defensible bridge that demonstrates source-to-OMOP transformation without claiming vocabulary standardization or full CDM conformance.

## Requirements

- Shape qualified canonical data as OMOP CDM v5.4 PERSON, OBSERVATION_PERIOD, VISIT_OCCURRENCE, CONDITION_OCCURRENCE, PROCEDURE_OCCURRENCE, MEASUREMENT, DRUG_EXPOSURE, and PAYER_PLAN_PERIOD views.
- Assign stable integer IDs while retaining a direct source-identifier bridge.
- Merge overlapping or adjacent Coverage periods into non-overlapping observation periods.
- Derive an explicitly labeled clinical-event span only when Coverage is unavailable.
- Retain source codes and use concept ID `0` where no governed Standard Concept mapping exists.
- Map only controlled Encounter classes to reviewed Visit Standard Concepts.
- Reconcile every qualified source domain to its OMOP-compatible view.
- Export row reconciliation and vocabulary-mapping status to the dashboard contract.
- Persist critical relationship/reconciliation controls and a non-blocking vocabulary-gap warning.
- State clearly that the subset is not an OMOP-conformant CDM instance.

## Acceptance criteria

1. All eight source/view domain counts reconcile exactly.
2. Every OMOP PERSON has at least one non-overlapping OBSERVATION_PERIOD.
3. Every event resolves to PERSON and every populated visit key resolves to VISIT_OCCURRENCE.
4. Repeated identifier refreshes preserve existing IDs and do not add duplicates.
5. Controlled `IMP`, `AMB`, and `EMER` classes map to concepts 9201, 9202, and 9203.
6. Unmapped source terminology remains visible as a warning and in a dashboard dataset.
7. Automated tests, independent validation SQL, dashboard export, and the persistent gate pass with zero blocking results.

Status: complete as an OMOP-compatible analytical subset; full OMOP conformance remains explicitly out of scope.
