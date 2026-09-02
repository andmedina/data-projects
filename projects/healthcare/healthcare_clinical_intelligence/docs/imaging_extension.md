# Imaging Metadata Extension

The implemented controlled profile ingests FHIR `ImagingStudy` metadata through the immutable raw FHIR path. It normalizes one study header and one or more series rows, retaining patient/encounter relationships, status/start time, study and series UIDs, synthetic accession identifier, DICOM modality code, body-site code, and declared series/instance counts.

No DICOM pixel data, rendered images, encapsulated documents, or binary FHIR resources are generated, ingested, or stored. DICOM UIDs are technical identifiers, not privacy controls; only invented synthetic identifiers are permitted.

The gate reconciles declared study series counts to normalized series, declared study instance counts to series totals, and requires a modality on every series. `mart.imaging_activity_monthly` reports metadata volumes without image interpretation.

DiagnosticReport/order linkage, DICOMweb/PACS transport, SOP-class metadata, de-identification validation, and image ML remain future work requiring explicit source/interface contracts.
