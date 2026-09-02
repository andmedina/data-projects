# DE-010 Solution

FHIR validation now accepts ImagingStudy only when status, start time, subject, series UID, and series modality are present. Latest-version staging separates the study header from its series array. Core loading resolves patient/encounter references, upserts the header, and rebuilds the derived series collection so removed source series cannot remain stale.

Three critical controls reconcile header series count, header instance count, and modality completeness. The dashboard mart aggregates only metadata volumes. Pixel data, Binary resources, clinical interpretations, DICOMweb transport, and PACS access remain outside this implementation.
