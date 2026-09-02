"""Dependency-free HL7 v2 parsing for controlled synthetic messages."""

from __future__ import annotations

from datetime import datetime
from typing import Any

ADT_EVENT_STATES = {
    "A01": "admitted",
    "A02": "transferred",
    "A03": "discharged",
    "A08": "updated",
}
SUPPORTED_MESSAGE_TYPES = {
    *(f"ADT^{event}" for event in ADT_EVENT_STATES),
    "ORM^O01",
    "ORU^R01",
}
SUPPORTED_ORDER_CONTROLS = {"NW", "CA", "DC", "XO", "SC"}


def _field(segment: list[str] | None, position: int) -> str | None:
    if segment is None or len(segment) <= position:
        return None
    return segment[position] or None


def _component(value: str | None, position: int = 0) -> str | None:
    if not value:
        return None
    components = value.split("^")
    if len(components) <= position:
        return None
    return components[position] or None


def _parse_timestamp(value: str | None) -> str | None:
    """Normalize the controlled HL7 DTM precisions to an ISO timestamp."""
    if not value:
        return None
    for length, format_string in (
        (14, "%Y%m%d%H%M%S"),
        (12, "%Y%m%d%H%M"),
        (10, "%Y%m%d%H"),
        (8, "%Y%m%d"),
    ):
        candidate = value[:length]
        if len(candidate) != length:
            continue
        try:
            return datetime.strptime(candidate, format_string).isoformat()
        except ValueError:
            continue
    return None


def _empty_result(errors: list[str]) -> dict[str, Any]:
    return {
        "errors": errors,
        "message_type": None,
        "message_control_id": None,
        "message_event_at": None,
        "patient_id": None,
        "encounter_event": None,
        "observations": [],
        "orders": [],
    }


def parse_message(message: str) -> dict[str, Any]:
    """Parse the repository's ADT, ORM, and ORU profiles into normalized events."""
    segments = [line.split("|") for line in message.strip().replace("\r", "\n").split("\n") if line]
    segments_by_name: dict[str, list[list[str]]] = {}
    for segment in segments:
        segments_by_name.setdefault(segment[0], []).append(segment)

    msh = next(iter(segments_by_name.get("MSH", [])), None)
    if not msh:
        return _empty_result(["MISSING_MSH"])

    errors: list[str] = []
    message_type = _field(msh, 8)
    message_control_id = _field(msh, 9)
    message_timestamp = _field(msh, 6)
    message_event_at = _parse_timestamp(message_timestamp)
    if not message_type:
        errors.append("MISSING_MESSAGE_TYPE")
    elif message_type not in SUPPORTED_MESSAGE_TYPES:
        errors.append("UNSUPPORTED_MESSAGE_TYPE")
    if not message_control_id:
        errors.append("MISSING_MESSAGE_CONTROL_ID")
    if not message_timestamp:
        errors.append("MISSING_MESSAGE_TIMESTAMP")
    elif not message_event_at:
        errors.append("INVALID_MESSAGE_TIMESTAMP")

    pid = next(iter(segments_by_name.get("PID", [])), None)
    patient_id = _component(_field(pid, 3))
    if not patient_id:
        errors.append("MISSING_PATIENT_ID")

    pv1 = next(iter(segments_by_name.get("PV1", [])), None)
    encounter_id = _component(_field(pv1, 19))
    encounter_event = None
    if message_type and message_type.startswith("ADT^"):
        if not pv1:
            errors.append("MISSING_PV1")
        if not encounter_id:
            errors.append("MISSING_ENCOUNTER_ID")
        event_code = _component(message_type, 1)
        patient_class = _field(pv1, 2)
        assigned_location = _field(pv1, 3)
        prior_location = _field(pv1, 6)
        if not patient_class:
            errors.append("MISSING_PATIENT_CLASS")
        if event_code in {"A01", "A02"} and not assigned_location:
            errors.append("MISSING_ASSIGNED_LOCATION")
        if event_code == "A02" and not prior_location:
            errors.append("MISSING_PRIOR_LOCATION")
        event_state = ADT_EVENT_STATES.get(event_code or "")
        if event_state:
            encounter_event = {
                "encounter_id": encounter_id,
                "event_code": event_code,
                "event_state": event_state,
                "patient_class": patient_class,
                "assigned_location": assigned_location,
                "prior_location": prior_location,
                "event_at": message_event_at,
            }
    if message_type == "ORM^O01":
        if not pv1:
            errors.append("MISSING_PV1")
        if not encounter_id:
            errors.append("MISSING_ENCOUNTER_ID")
        if not _field(pv1, 2):
            errors.append("MISSING_PATIENT_CLASS")

    observations = []
    for segment in segments_by_name.get("OBX", []):
        observation = {
            "set_id": _field(segment, 1),
            "value_type": _field(segment, 2),
            "code": _component(_field(segment, 3)),
            "value": _field(segment, 5),
            "units": _field(segment, 6),
            "status": _field(segment, 11),
        }
        if not observation["set_id"]:
            errors.append("MISSING_OBX_SET_ID")
        if not observation["code"]:
            errors.append("MISSING_OBX_CODE")
        observations.append(observation)
    if message_type == "ORU^R01" and not observations:
        errors.append("MISSING_OBX")

    orders = []
    current_orc: list[str] | None = None
    for segment in segments:
        if segment[0] == "ORC":
            current_orc = segment
            continue
        if segment[0] != "OBR" or message_type != "ORM^O01":
            continue
        service = _field(segment, 4)
        order = {
            "order_id": _field(current_orc, 2) or _field(segment, 2),
            "order_control": _field(current_orc, 1),
            "order_status": _field(current_orc, 5),
            "code": _component(service),
            "code_display": _component(service, 1),
            "code_system": _component(service, 2),
            "ordered_at": _parse_timestamp(_field(segment, 7)) or message_event_at,
            "encounter_id": encounter_id,
        }
        if not order["order_id"]:
            errors.append("MISSING_ORDER_ID")
        if not order["order_control"]:
            errors.append("MISSING_ORDER_CONTROL")
        elif order["order_control"] not in SUPPORTED_ORDER_CONTROLS:
            errors.append("INVALID_ORDER_CONTROL")
        if not order["code"]:
            errors.append("MISSING_ORDER_CODE")
        orders.append(order)
    if message_type == "ORM^O01" and not orders:
        errors.append("MISSING_ORDER")

    return {
        "errors": list(dict.fromkeys(errors)),
        "message_type": message_type,
        "message_control_id": message_control_id,
        "message_event_at": message_event_at,
        "patient_id": patient_id,
        "encounter_event": encounter_event,
        "observations": observations,
        "orders": orders,
    }
