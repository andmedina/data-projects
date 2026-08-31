# Data Sources

## Required source: Synthea

Synthea generates synthetic patient records and FHIR R4 resources. Version, generation command, seed (when available), resource counts, and export timestamp must be recorded for every project dataset.

Generated bulk files belong in `data/synthetic/`, which is ignored by Git. Only tiny, hand-reviewed synthetic fixtures belong in `data/samples/`.

## Optional source: HAPI FHIR

HAPI FHIR is used only to demonstrate REST retrieval, pagination, and incremental query behavior after file-based loading works. It is not a required dependency for initial development.

## Controlled interoperability fixtures

Small hand-authored HL7 v2 and claims CSV files exercise non-FHIR integration paths. `claims_expanded.csv` contains invented payer/provider identifiers, ordered diagnosis/procedure codes, adjustments, and original/replacement lineage. These fixtures demonstrate the repository's normalized contracts; they are not copied from real transactions and are not certified X12/HL7 implementations.

## Data handling policy

No real patient data, PHI, clinical exports, or access credentials may be added to this repository.
