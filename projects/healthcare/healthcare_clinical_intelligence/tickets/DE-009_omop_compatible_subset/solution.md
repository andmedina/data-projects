# DE-009 Solution

The new `omop` schema uses views with OMOP CDM v5.4 column shapes over the canonical model. `omop.entity_id_map` assigns stable integer identifiers by entity type and canonical source ID; ordered, conflict-safe refreshes preserve existing IDs while adding new qualified records. The FHIR/core pipeline and Airflow core-load path refresh those mappings automatically, and `omop-refresh` provides an explicit operator command.

Coverage is the preferred source for OBSERVATION_PERIOD. A gaps-and-islands transformation merges overlapping and adjacent periods across payers. Patients without Coverage receive one visibly labeled `clinical_event_span` from the earliest through latest canonical event, which closes the required PERSON-to-OBSERVATION_PERIOD relationship without presenting inferred enrollment as source enrollment.

Encounter classes use the controlled Visit mappings `IMP`→9201, `AMB`→9202, and `EMER`→9203. Other clinical, demographic, unit, provenance, and payer concepts remain `0`, while source systems, codes, values, and units are retained where the v5.4 shape permits. A vocabulary-status view and warning control ensure that missing Athena mappings cannot be mistaken for completed standardization.

The MedicationRequest-to-DRUG_EXPOSURE view is an order-date compatibility proxy. Its start and end are the authored date; it is not proof that a drug was dispensed, administered, or taken and must not be used for medication exposure research.
