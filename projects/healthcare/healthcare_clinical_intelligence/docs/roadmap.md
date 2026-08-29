# Roadmap

## Phase 1 — FHIR clinical foundation

1. Define PostgreSQL schemas and load metadata.
2. Ingest FHIR Patient, Encounter, and Observation resources to raw storage.
3. Build staging transformations, validation rules, quarantine, and reference resolution.
4. Build canonical entities, reconciliation reporting, and ED-utilization mart.
5. Deliver DE-001 through DE-006 evidence and test coverage.

## Later phases

| Phase | Outcome |
| --- | --- |
| 2. Analytics | Dimensional marts, KPI dictionary, Power BI, analyst tickets |
| 3. Claims | Claim/claim-line model, payer costs, reconciliation |
| 4. HL7 v2 | ADT, ORU, ORM parsing and canonical mappings |
| 5. Data science | Temporally valid readmission cohort and reproducible baseline model |
| 6. Quality/population health | Quality measures and utilization/risk workflows |
| 7. OMOP | Partial mapping to OMOP CDM |
| 8. Imaging | ImagingStudy, radiology metadata, and DICOM concepts |

Each phase begins only after the preceding one is reproducible, tested, and documented.
