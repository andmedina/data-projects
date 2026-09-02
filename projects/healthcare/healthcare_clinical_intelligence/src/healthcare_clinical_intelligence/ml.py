"""Temporal cohort construction for synthetic readmission-model demonstrations."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_readmission_cohort(accepted_path: Path) -> list[dict[str, Any]]:
    patients: dict[str, dict[str, Any]] = {}
    encounters_by_patient: dict[str, list[dict[str, Any]]] = {}
    with accepted_path.open() as handle:
        for line in handle:
            record = json.loads(line)["canonical"]
            if record["resource_type"] == "Patient":
                patients[record["source_resource_id"]] = record
            elif record["resource_type"] == "Encounter" and record.get("start_at") and record.get("end_at"):
                encounters_by_patient.setdefault(record["patient_id"], []).append(record)
    cohort: list[dict[str, Any]] = []
    for patient_id, encounters in encounters_by_patient.items():
        encounters.sort(key=lambda encounter: encounter["start_at"])
        for index, encounter in enumerate(encounters):
            if encounter.get("encounter_class") != "IMP":
                continue
            prediction_at = _parse_time(encounter["end_at"])
            outcome_end = prediction_at + timedelta(days=30)
            future_inpatient = any(
                later.get("encounter_class") == "IMP" and prediction_at < _parse_time(later["start_at"]) <= outcome_end
                for later in encounters[index + 1 :]
            )
            history = [prior for prior in encounters[:index] if _parse_time(prior["end_at"]) <= prediction_at]
            birth_date = patients.get(patient_id, {}).get("birth_date")
            age = prediction_at.date().year - date.fromisoformat(birth_date).year if birth_date else None
            cohort.append(
                {
                    "index_encounter_id": encounter["source_resource_id"],
                    "patient_id": patient_id,
                    "prediction_at": encounter["end_at"],
                    "prior_encounter_count": len(history),
                    "prior_ed_count": sum(item.get("encounter_class") == "EMER" for item in history),
                    "age_at_prediction": age,
                    "readmitted_within_30_days": int(future_inpatient),
                }
            )
    return cohort


def export_readmission_cohort(accepted_path: Path, output_path: Path) -> list[dict[str, Any]]:
    rows = build_readmission_cohort(accepted_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "index_encounter_id",
        "patient_id",
        "prediction_at",
        "prior_encounter_count",
        "prior_ed_count",
        "age_at_prediction",
        "readmitted_within_30_days",
    ]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return rows
