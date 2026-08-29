"""Small, dependency-free HL7 v2 parser for controlled synthetic messages."""

from __future__ import annotations

from typing import Any


def parse_message(message: str) -> dict[str, Any]:
    segments = [line.split("|") for line in message.strip().replace("\r", "\n").split("\n") if line]
    by_name = {segment[0]: segment for segment in segments}
    errors: list[str] = []
    msh = by_name.get("MSH")
    if not msh:
        return {"errors": ["MISSING_MSH"], "message_type": None, "patient_id": None, "observations": []}
    message_type = msh[8] if len(msh) > 8 else None
    message_control_id = msh[9] if len(msh) > 9 else None
    pid = by_name.get("PID")
    patient_id = pid[3].split("^")[0] if pid and len(pid) > 3 else None
    if not patient_id:
        errors.append("MISSING_PATIENT_ID")
    observations = []
    for segment in segments:
        if segment[0] == "OBX":
            observations.append({
                "set_id": segment[1] if len(segment) > 1 else None,
                "value_type": segment[2] if len(segment) > 2 else None,
                "code": segment[3].split("^")[0] if len(segment) > 3 else None,
                "value": segment[5] if len(segment) > 5 else None,
                "units": segment[6] if len(segment) > 6 else None,
                "status": segment[11] if len(segment) > 11 else None,
            })
    return {"errors": errors, "message_type": message_type, "message_control_id": message_control_id, "patient_id": patient_id, "observations": observations}
