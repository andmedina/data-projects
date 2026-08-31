# Roadmap

## Delivered foundation

- FHIR file, REST, incremental-checkpoint, PostgreSQL, and Airflow workflows.
- Canonical patient, encounter, observation, condition, procedure, medication, provider, organization, and coverage entities.
- Controlled claims header/detail, payer/provider dimensions, ordered diagnosis/procedure codes, adjustment lineage, and HL7 ORU result paths.
- Reconciliation, quarantine, quality controls, and idempotent reruns.
- Persistent threshold-based quality history and an Airflow-blocking critical gate.
- Typed FHIR laboratory result lineage, completeness mart, and a reproduced missing-result incident with recovery evidence.
- ED activity, clinical activity, claims-cost marts, and dashboard export contract.
- Temporally valid readmission cohort and reproducible baseline model.

## Next extensions

| Phase | Outcome |
| --- | --- |
| Dashboard client | Build the Power BI file from the stable export contract and apply final visual-design choices |
| Claims EDI hardening | Add trading-partner-specific X12 837/835 envelopes, acknowledgements, and code-set governance when a synthetic interchange contract is selected |
| HL7 v2 expansion | Add ADT lifecycle state and ORM order mappings beyond controlled validation |
| Model governance | Add experiment tracking, calibration monitoring, subgroup review, and approval controls |
| Quality/population health | Add eligibility-aware measures and utilization/risk workflows |
| OMOP | Map a documented subset to OMOP CDM with vocabulary handling |
| Imaging | Model ImagingStudy/radiology metadata and DICOM concepts without storing image pixels |

Extensions should preserve the same source-fidelity, reconciliation, synthetic-only, and independent-validation standards.
