# Data Sources

## Required source: Synthea

Synthea generates synthetic patient records and FHIR R4 resources. Version, generation command, seed (when available), resource counts, and export timestamp must be recorded for every project dataset.

Generated bulk files belong in `data/synthetic/`, which is ignored by Git. Only tiny, hand-reviewed synthetic fixtures belong in `data/samples/`.

## Optional source: HAPI FHIR

HAPI FHIR is used only to demonstrate REST retrieval, pagination, and incremental query behavior after file-based loading works. It is not a required dependency for initial development.

## Data handling policy

No real patient data, PHI, clinical exports, or access credentials may be added to this repository.
