"""Local, file-based runner used for reproducible synthetic FHIR demonstrations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .claims import iter_validated_claim_rows
from .fhir import iter_resources, normalize_resource, validate_resource
from .hl7 import parse_message


def run_fhir_file(input_path: Path, output_dir: Path) -> dict[str, int]:
    payload = json.loads(input_path.read_text())
    output_dir.mkdir(parents=True, exist_ok=True)
    accepted, rejected, seen = [], [], set()
    for resource in iter_resources(payload):
        errors = validate_resource(resource)
        fingerprint = hashlib.sha256(json.dumps(resource, sort_keys=True).encode()).hexdigest()
        key = (resource.get("resourceType"), resource.get("id"), fingerprint)
        if key in seen:
            continue
        seen.add(key)
        if errors:
            rejected.append({"reason_codes": errors, "payload": resource})
        else:
            accepted.append({"payload_sha256": fingerprint, "raw": resource, "canonical": normalize_resource(resource)})
    (output_dir / "accepted.jsonl").write_text("".join(json.dumps(row) + "\n" for row in accepted))
    (output_dir / "quarantine.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rejected))
    report = {"source_records": len(seen), "accepted": len(accepted), "rejected": len(rejected)}
    (output_dir / "run_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def run_claims_file(input_path: Path, output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    accepted, rejected = [], []
    for row, errors in iter_validated_claim_rows(input_path):
        (rejected if errors else accepted).append({"reason_codes": errors, "payload": row} if errors else row)
    (output_dir / "accepted_claims.jsonl").write_text("".join(json.dumps(row) + "\n" for row in accepted))
    (output_dir / "quarantine_claims.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rejected))
    report = {"source_records": len(accepted) + len(rejected), "accepted": len(accepted), "rejected": len(rejected)}
    (output_dir / "claims_run_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def run_hl7_file(input_path: Path, output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    messages = [part for part in input_path.read_text().strip().split("\n\n") if part.strip()]
    parsed = [parse_message(message) for message in messages]
    accepted = [message for message in parsed if not message["errors"]]
    rejected = [message for message in parsed if message["errors"]]
    (output_dir / "accepted_hl7.jsonl").write_text("".join(json.dumps(row) + "\n" for row in accepted))
    (output_dir / "quarantine_hl7.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rejected))
    report = {"source_records": len(parsed), "accepted": len(accepted), "rejected": len(rejected)}
    (output_dir / "hl7_run_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
