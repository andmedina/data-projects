# DE-010 — Normalize Metadata-Only ImagingStudy Records

## Requirements

- Accept a controlled synthetic FHIR ImagingStudy profile.
- Preserve immutable raw JSON and normalize study header and series grains.
- Link studies to known patients and encounters.
- Retain synthetic study/series UIDs, accession, modality, body site, and declared counts.
- Reconcile declared series and instance totals and require series modality.
- Export monthly metadata activity without storing or interpreting pixels.

## Acceptance criteria

1. The 100-patient fixture adds 25 valid studies with zero rejects.
2. Core contains 25 study and 25 series rows with resolved clinical links.
3. Declared series/instance counts reconcile and all modalities are populated.
4. Independent validation and the persistent gate have zero blocking results.
5. No pixel or Binary resource is introduced.

Status: complete for the controlled metadata-only profile.
