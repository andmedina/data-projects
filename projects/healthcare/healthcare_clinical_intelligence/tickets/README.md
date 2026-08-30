# Job-Simulation Tickets

Tickets capture business context, investigation, solution, validation, and stakeholder communication. They are implementation evidence, not invented incidents. A ticket is marked complete only when its acceptance criteria and prevention controls are demonstrated.

The repository foundation supports DE-001 and DE-002 implementation work. Ticket completion still requires saved run evidence, reconciliation output, and validation against the live database/API environment.

Implemented ticket evidence:

- `DE-001` FHIR Patient and Encounter ingestion
- `DE-002` Incremental, idempotent FHIR loading
- `DE-003` FHIR reference resolution
- `DE-004` Source-to-warehouse reconciliation
- `DE-005` Persistent clinical data-quality controls and Airflow gate
- `DE-006` Missing laboratory-result incident, typed Observation remediation, and prevention controls
- `DA-001` Emergency-department activity mart, independent validation, and stakeholder interpretation
- `DS-001` Temporally valid 30-day readmission baseline

Future tickets can extend the same evidence pattern to late-arriving results, reference-range normalization, and source-specific terminology defects.
