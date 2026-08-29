# Job-Simulation Tickets

Tickets capture business context, investigation, solution, validation, and stakeholder communication. They are implementation evidence, not invented incidents. A ticket is marked complete only when its acceptance criteria and prevention controls are demonstrated.

The repository foundation supports DE-001 and DE-002 implementation work. Ticket completion still requires saved run evidence, reconciliation output, and validation against the live database/API environment.

Implemented ticket evidence:

- `DE-001` FHIR Patient and Encounter ingestion
- `DE-002` Incremental, idempotent FHIR loading
- `DE-003` FHIR reference resolution
- `DE-004` Source-to-warehouse reconciliation
- `DA-001` Emergency-department activity mart, independent validation, and stakeholder interpretation
- `DS-001` Temporally valid 30-day readmission baseline

The later DE-005 clinical data-quality framework and DE-006 missing-results investigation remain candidates for deeper operational simulations.
