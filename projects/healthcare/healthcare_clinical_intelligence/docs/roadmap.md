# Roadmap

## Delivered foundation

- FHIR file, REST, incremental-checkpoint, PostgreSQL, and Airflow workflows.
- Canonical patient, encounter, observation, condition, procedure, medication, provider, organization, and coverage entities.
- Controlled claims header/detail, payer/provider dimensions, ordered diagnosis/procedure codes, and adjustment lineage.
- HL7 ADT lifecycle, ORM order, and ORU result event paths with current-state marts and reconciliation controls.
- Reconciliation, quarantine, quality controls, and idempotent reruns.
- Persistent threshold-based quality history and an Airflow-blocking critical gate.
- Typed FHIR laboratory result lineage, completeness mart, and a reproduced missing-result incident with recovery evidence.
- ED activity, clinical activity, claims-cost marts, and dashboard export contract.
- Typed Coverage periods, distinct payer member-month denominators, and eligibility-aware ED utilization.
- Source-preserving OMOP v5.4-compatible PERSON, observation-period, visit, clinical-event, and payer-plan views with stable IDs and reconciliation.
- Metadata-only FHIR ImagingStudy header/series model, DICOM modality/body-site fields, count controls, and activity mart.
- Temporally valid readmission cohort, reproducible baseline model, calibration/subgroup evidence, experiment registry, model card, and synthetic-demo approval gate.
- Monorepo-root CI with linting, formatting, typing, coverage, dependency updates, and a live PostgreSQL end-to-end job.
- Checksum-tracked schema application, durable pipeline failure/count metadata, stale-run controls, versioned dashboard checksums, and performance smoke tests.

## Next extensions

| Phase | Outcome |
| --- | --- |
| Dashboard client | Build the Power BI file from the stable export contract and apply final visual-design choices |
| Claims EDI hardening | Add trading-partner-specific X12 837/835 envelopes, acknowledgements, and code-set governance when a synthetic interchange contract is selected |
| HL7 interface hardening | Add interface-specific profiles, ACK/NACK handling, MLLP transport, escape/repetition rules, and timezone variants |
| Model lifecycle hardening | Add external validation, confidence intervals, drift monitoring, accountable reviewers, and retraining/decommission controls when a non-synthetic use case exists |
| Population-health hardening | Add continuous-enrollment rules, partial-month policy, risk adjustment, and an authoritative encounter-to-coverage attribution contract |
| OMOP conformance | Load a governed Athena vocabulary release, complete required CDM tables, and run OHDSI Data Quality Dashboard/Achilles validation |
| Imaging hardening | Add governed DiagnosticReport/order linkage, DICOMweb transport, SOP-class metadata, and synthetic de-identification validation when an interface contract exists |

Extensions should preserve the same source-fidelity, reconciliation, synthetic-only, and independent-validation standards.
