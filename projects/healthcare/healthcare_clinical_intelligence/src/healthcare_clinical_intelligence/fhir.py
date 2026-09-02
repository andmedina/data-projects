"""FHIR R4 extraction and validation helpers for the Phase 1 clinical flow."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

SUPPORTED_RESOURCES = {
    "Patient", "Encounter", "Observation", "Condition", "Procedure",
    "MedicationRequest", "Practitioner", "Organization", "Coverage",
    "ImagingStudy",
}
PATIENT_SCOPED_RESOURCES = {"Encounter", "Observation", "Condition", "Procedure", "MedicationRequest", "Coverage", "ImagingStudy"}
OBSERVATION_VALUE_KEYS = {
    "valueQuantity", "valueString", "valueBoolean", "valueInteger", "valueCodeableConcept",
}


def iter_resources(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Yield resources from a FHIR Bundle or an individual resource."""
    if payload.get("resourceType") == "Bundle":
        for entry in payload.get("entry", []):
            resource = entry.get("resource")
            if isinstance(resource, dict):
                yield resource
    else:
        yield payload


def reference_id(reference: str | None) -> str | None:
    """Extract the terminal FHIR id from relative or absolute references."""
    if not reference:
        return None
    clean = reference.rstrip("/")
    if "/" not in clean:
        return clean
    return clean.rsplit("/", 1)[-1] or None


def first_coding(concept: dict[str, Any] | None) -> dict[str, str | None]:
    coding = (concept or {}).get("coding") or []
    if not coding:
        return {"system": None, "code": None, "display": (concept or {}).get("text")}
    item = coding[0]
    return {"system": item.get("system"), "code": item.get("code"), "display": item.get("display") or (concept or {}).get("text")}


def validate_resource(resource: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    resource_type = resource.get("resourceType")
    if resource_type not in SUPPORTED_RESOURCES:
        errors.append("UNSUPPORTED_RESOURCE_TYPE")
        return errors
    if not resource.get("id"):
        errors.append("MISSING_RESOURCE_ID")
    if resource_type in PATIENT_SCOPED_RESOURCES and not (resource.get("subject") or resource.get("beneficiary") or {}).get("reference"):
        errors.append(f"MISSING_{resource_type.upper()}_SUBJECT")
    if resource_type == "Observation":
        if not resource.get("status"):
            errors.append("MISSING_OBSERVATION_STATUS")
        unsupported_value_keys = {key for key in resource if key.startswith("value")} - OBSERVATION_VALUE_KEYS
        if unsupported_value_keys:
            errors.append("UNSUPPORTED_OBSERVATION_VALUE_TYPE")
        value_keys = OBSERVATION_VALUE_KEYS.intersection(resource)
        if len(value_keys) > 1:
            errors.append("MULTIPLE_OBSERVATION_VALUES")
        if value_keys and resource.get("dataAbsentReason"):
            errors.append("OBSERVATION_VALUE_AND_ABSENT_REASON")
        quantity = resource.get("valueQuantity")
        if quantity is not None:
            if not isinstance(quantity, dict):
                errors.append("INVALID_OBSERVATION_QUANTITY")
            quantity_value = quantity.get("value") if isinstance(quantity, dict) else None
            if quantity_value is not None and (isinstance(quantity_value, bool) or not isinstance(quantity_value, (int, float))):
                errors.append("INVALID_OBSERVATION_QUANTITY_VALUE")
    if resource_type == "Coverage":
        period_payload = resource.get("period")
        period = period_payload if isinstance(period_payload, dict) else {}
        start = period.get("start")
        end = period.get("end")
        if not resource.get("status"):
            errors.append("MISSING_COVERAGE_STATUS")
        payors = resource.get("payor") or []
        if not payors or not isinstance(payors[0], dict) or not payors[0].get("reference"):
            errors.append("MISSING_COVERAGE_PAYOR")
        if not start:
            errors.append("MISSING_COVERAGE_PERIOD_START")
        if not end:
            errors.append("MISSING_COVERAGE_PERIOD_END")
        if period_payload is not None and not isinstance(period_payload, dict):
            errors.append("INVALID_COVERAGE_PERIOD")
        if start and end:
            try:
                if date.fromisoformat(end[:10]) < date.fromisoformat(start[:10]):
                    errors.append("INVALID_COVERAGE_PERIOD")
            except (TypeError, ValueError):
                errors.append("INVALID_COVERAGE_PERIOD")
    if resource_type == "ImagingStudy":
        if not resource.get("status"):
            errors.append("MISSING_IMAGING_STUDY_STATUS")
        if not resource.get("started"):
            errors.append("MISSING_IMAGING_STUDY_STARTED")
        series = resource.get("series") or []
        if not series:
            errors.append("MISSING_IMAGING_STUDY_SERIES")
        for item in series:
            if not isinstance(item, dict) or not item.get("uid"):
                errors.append("MISSING_IMAGING_SERIES_UID")
            if not isinstance(item, dict) or not (item.get("modality") or {}).get("code"):
                errors.append("MISSING_IMAGING_SERIES_MODALITY")
    return errors


def normalize_resource(resource: dict[str, Any]) -> dict[str, Any]:
    """Return a small canonical record while leaving original JSON in raw storage."""
    resource_type = resource["resourceType"]
    base = {"resource_type": resource_type, "source_resource_id": resource["id"]}
    if resource_type == "Patient":
        return base | {
            "birth_date": resource.get("birthDate"),
            "sex": resource.get("gender"),
            "deceased": resource.get("deceasedBoolean", False),
        }
    if resource_type == "Encounter":
        period = resource.get("period") or {}
        return base | {
            "patient_id": reference_id((resource.get("subject") or {}).get("reference")),
            "status": resource.get("status"),
            "encounter_class": ((resource.get("class") or {}).get("code")),
            "encounter_type": first_coding((resource.get("type") or [{}])[0]),
            "start_at": period.get("start"),
            "end_at": period.get("end"),
        }
    if resource_type == "Organization":
        return base | {"name": resource.get("name"), "organization_type": first_coding((resource.get("type") or [{}])[0])}
    if resource_type == "Practitioner":
        name = (resource.get("name") or [{}])[0]
        return base | {"name": " ".join(part for part in [name.get("given", [None])[0], name.get("family")] if part)}
    if resource_type == "Coverage":
        period = resource.get("period") or {}
        return base | {
            "patient_id": reference_id((resource.get("beneficiary") or {}).get("reference")),
            "payer_id": reference_id((resource.get("payor") or [{}])[0].get("reference")),
            "status": resource.get("status"),
            "coverage_start": period.get("start"),
            "coverage_end": period.get("end"),
        }
    if resource_type == "ImagingStudy":
        identifiers = resource.get("identifier") or []
        study_uid = next(
            (identifier.get("value") for identifier in identifiers if identifier.get("system") == "urn:dicom:uid"),
            None,
        )
        accession = next(
            (identifier.get("value") for identifier in identifiers if identifier.get("system") != "urn:dicom:uid"),
            None,
        )
        return base | {
            "patient_id": reference_id((resource.get("subject") or {}).get("reference")),
            "encounter_id": reference_id((resource.get("encounter") or {}).get("reference")),
            "status": resource.get("status"),
            "started_at": resource.get("started"),
            "study_uid": study_uid,
            "accession_identifier": accession,
            "number_of_series": resource.get("numberOfSeries"),
            "number_of_instances": resource.get("numberOfInstances"),
            "series": [
                {
                    "series_uid": item.get("uid"),
                    "series_number": item.get("number"),
                    "modality": {
                        "system": (item.get("modality") or {}).get("system"),
                        "code": (item.get("modality") or {}).get("code"),
                        "display": (item.get("modality") or {}).get("display"),
                    },
                    "body_site": {
                        "system": (item.get("bodySite") or {}).get("system"),
                        "code": (item.get("bodySite") or {}).get("code"),
                        "display": (item.get("bodySite") or {}).get("display"),
                    },
                    "number_of_instances": item.get("numberOfInstances"),
                }
                for item in resource.get("series") or []
            ],
        }
    if resource_type in {"Condition", "Procedure", "MedicationRequest"}:
        subject = resource.get("subject") or {}
        concept = resource.get("code") or resource.get("medicationCodeableConcept")
        return base | {
            "patient_id": reference_id(subject.get("reference")),
            "encounter_id": reference_id((resource.get("encounter") or {}).get("reference")),
            "status": resource.get("clinicalStatus", {}).get("coding", [{}])[0].get("code") or resource.get("status"),
            "code": first_coding(concept),
            "recorded_at": resource.get("recordedDate") or resource.get("performedDateTime") or resource.get("authoredOn"),
        }
    value_keys = OBSERVATION_VALUE_KEYS.intersection(resource)
    value_key = next(iter(value_keys), None)
    quantity_payload = resource.get("valueQuantity")
    quantity = quantity_payload if isinstance(quantity_payload, dict) else {}
    coded_value = first_coding(resource.get("valueCodeableConcept"))
    return base | {
        "patient_id": reference_id((resource.get("subject") or {}).get("reference")),
        "encounter_id": reference_id((resource.get("encounter") or {}).get("reference")),
        "status": resource.get("status"),
        "code": first_coding(resource.get("code")),
        "category": first_coding((resource.get("category") or [{}])[0]),
        "effective_at": resource.get("effectiveDateTime"),
        "value_type": value_key.removeprefix("value") if value_key else None,
        "value_numeric": quantity.get("value") if value_key == "valueQuantity" else resource.get("valueInteger"),
        "value_text": resource.get("valueString"),
        "value_boolean": resource.get("valueBoolean"),
        "value_code": coded_value if value_key == "valueCodeableConcept" else None,
        "unit": quantity.get("unit"),
        "unit_system": quantity.get("system"),
        "unit_code": quantity.get("code"),
        "data_absent_reason": first_coding(resource.get("dataAbsentReason")),
    }
