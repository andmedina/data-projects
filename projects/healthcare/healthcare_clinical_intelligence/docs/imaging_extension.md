# Imaging Extension

Imaging is Phase 8. The platform will first ingest metadata—not pixel data—from FHIR `ImagingStudy`, `DiagnosticReport`, imaging orders, and DICOM headers. Pixel data is explicitly out of scope until secure synthetic imaging fixtures, storage controls, and a clear analytical or ML objective exist.

Core links are patient, encounter, imaging study, modality, body site, report, and accession/study identifiers. DICOM UIDs are technical identifiers, not substitutes for privacy controls.
