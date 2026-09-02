"""Portable analytical exports derived from accepted canonical pipeline records."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any


def ed_utilization_from_accepted(accepted_path: Path, output_path: Path) -> list[dict[str, Any]]:
    encounters: dict[str, list[str]] = defaultdict(list)
    with accepted_path.open() as handle:
        for line in handle:
            canonical = json.loads(line)["canonical"]
            if (
                canonical["resource_type"] == "Encounter"
                and canonical.get("encounter_class") == "EMER"
                and canonical.get("status") in {"finished", "completed"}
                and canonical.get("start_at")
            ):
                encounters[canonical["start_at"][:7]].append(canonical["patient_id"])
    rows = [
        {
            "reporting_month": month,
            "ed_encounters": len(patient_ids),
            "patients_with_ed_encounter": len(set(patient_ids)),
        }
        for month, patient_ids in sorted(encounters.items())
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["reporting_month", "ed_encounters", "patients_with_ed_encounter"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def _month_starts_inclusive(start: str, end: str) -> list[str]:
    """Return ISO year-month values touched by an inclusive date period."""
    current = date.fromisoformat(start[:10]).replace(day=1)
    final = date.fromisoformat(end[:10]).replace(day=1)
    months = []
    while current <= final:
        months.append(current.strftime("%Y-%m"))
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)
    return months


def eligible_ed_utilization_from_accepted(
    accepted_path: Path,
    output_path: Path,
) -> list[dict[str, Any]]:
    """Export ED encounters per 1,000 active-coverage member months by payer."""
    member_months: set[tuple[str, str | None, str]] = set()
    ed_encounters: list[tuple[str, str, str]] = []
    with accepted_path.open() as handle:
        for line in handle:
            canonical = json.loads(line)["canonical"]
            resource_type = canonical["resource_type"]
            if resource_type == "Coverage" and canonical.get("status") == "active":
                start = canonical.get("coverage_start")
                end = canonical.get("coverage_end")
                patient_id = canonical.get("patient_id")
                if start and end and patient_id:
                    for month in _month_starts_inclusive(start, end):
                        member_months.add((month, canonical.get("payer_id"), patient_id))
            elif (
                resource_type == "Encounter"
                and canonical.get("encounter_class") == "EMER"
                and canonical.get("status") in {"finished", "completed"}
                and canonical.get("start_at")
                and canonical.get("patient_id")
            ):
                ed_encounters.append(
                    (canonical["start_at"][:7], canonical["patient_id"], canonical["source_resource_id"])
                )

    members_by_group: dict[tuple[str, str | None], set[str]] = defaultdict(set)
    payers_by_member_month: dict[tuple[str, str], set[str | None]] = defaultdict(set)
    for month, payer_id, patient_id in member_months:
        members_by_group[(month, payer_id)].add(patient_id)
        payers_by_member_month[(month, patient_id)].add(payer_id)

    encounters_by_group: dict[tuple[str, str | None], list[tuple[str, str]]] = defaultdict(list)
    for month, patient_id, encounter_id in ed_encounters:
        for payer_id in payers_by_member_month.get((month, patient_id), set()):
            encounters_by_group[(month, payer_id)].append((encounter_id, patient_id))

    rows = []
    for group, patient_ids in sorted(members_by_group.items(), key=lambda item: (item[0][0], item[0][1] or "")):
        month, payer_id = group
        encounters = encounters_by_group.get(group, [])
        member_count = len(patient_ids)
        encounter_count = len(encounters)
        rows.append(
            {
                "reporting_month": month,
                "payer_organization_id": payer_id,
                "member_months": member_count,
                "ed_encounters": encounter_count,
                "patients_with_ed_encounter": len({patient_id for _, patient_id in encounters}),
                "ed_encounters_per_1000_member_months": round(1000 * encounter_count / member_count, 2),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "reporting_month",
        "payer_organization_id",
        "member_months",
        "ed_encounters",
        "patients_with_ed_encounter",
        "ed_encounters_per_1000_member_months",
    ]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def clinical_activity_from_accepted(accepted_path: Path, output_path: Path) -> list[dict[str, Any]]:
    """Export monthly condition, procedure, and medication-request counts."""
    activity: dict[str, dict[str, int]] = defaultdict(
        lambda: {"conditions": 0, "procedures": 0, "medication_requests": 0}
    )
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
        writer = csv.DictWriter(
            handle, fieldnames=["reporting_month", "conditions", "procedures", "medication_requests"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows
