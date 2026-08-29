"""FHIR R4 extraction and validation helpers for the Phase 1 clinical flow."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

SUPPORTED_RESOURCES = {"Patient", "Encounter", "Observation"}


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
    if resource_type == "Encounter" and not (resource.get("subject") or {}).get("reference"):
        errors.append("MISSING_ENCOUNTER_SUBJECT")
    if resource_type == "Observation":
        if not (resource.get("subject") or {}).get("reference"):
            errors.append("MISSING_OBSERVATION_SUBJECT")
        if not resource.get("status"):
            errors.append("MISSING_OBSERVATION_STATUS")
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
    value_keys = [key for key in resource if key.startswith("value")]
    value_key = value_keys[0] if value_keys else None
    return base | {
        "patient_id": reference_id((resource.get("subject") or {}).get("reference")),
        "encounter_id": reference_id((resource.get("encounter") or {}).get("reference")),
        "status": resource.get("status"),
        "code": first_coding(resource.get("code")),
        "effective_at": resource.get("effectiveDateTime"),
        "value_type": value_key,
        "value": resource.get(value_key) if value_key else None,
    }
