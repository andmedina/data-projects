"""Portable analytical exports derived from accepted canonical pipeline records."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def ed_utilization_from_accepted(accepted_path: Path, output_path: Path) -> list[dict[str, Any]]:
    encounters: dict[str, list[str]] = defaultdict(list)
    with accepted_path.open() as handle:
        for line in handle:
            canonical = json.loads(line)["canonical"]
            if canonical["resource_type"] == "Encounter" and canonical.get("encounter_class") == "EMER":
                encounters[canonical["start_at"][:7]].append(canonical["patient_id"])
    rows = [
        {"reporting_month": month, "ed_encounters": len(patient_ids), "patients_with_ed_encounter": len(set(patient_ids))}
        for month, patient_ids in sorted(encounters.items())
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["reporting_month", "ed_encounters", "patients_with_ed_encounter"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def clinical_activity_from_accepted(accepted_path: Path, output_path: Path) -> list[dict[str, Any]]:
    """Export monthly condition, procedure, and medication-request counts."""
    activity: dict[str, dict[str, int]] = defaultdict(lambda: {"conditions": 0, "procedures": 0, "medication_requests": 0})
    mapping = {
        "Condition": ("recorded_at", "conditions"),
        "Procedure": ("recorded_at", "procedures"),
        "MedicationRequest": ("recorded_at", "medication_requests"),
    }
    with accepted_path.open() as handle:
        for line in handle:
            canonical = json.loads(line)["canonical"]
            field = mapping.get(canonical["resource_type"])
            if field and canonical.get(field[0]):
                activity[canonical[field[0]][:7]][field[1]] += 1
    rows = [{"reporting_month": month} | values for month, values in sorted(activity.items())]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["reporting_month", "conditions", "procedures", "medication_requests"])
        writer.writeheader()
        writer.writerows(rows)
    return rows
