"""Controlled CSV claims validation for the payer integration."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from typing import Iterator

REQUIRED_COLUMNS = (
    "claim_id",
    "claim_line_id",
    "patient_id",
    "service_date",
    "billed_amount",
    "allowed_amount",
    "paid_amount",
)
BASE_AMOUNT_FIELDS = ("billed_amount", "allowed_amount", "paid_amount")
OPTIONAL_AMOUNT_FIELDS = ("patient_responsibility_amount", "adjustment_amount")
ADJUSTMENT_FREQUENCY_CODES = {"7", "8"}
VALID_FREQUENCY_CODES = {"1", *ADJUSTMENT_FREQUENCY_CODES}
NPI_PATTERN = re.compile(r"^\d{10}$")
CLAIM_HEADER_FIELDS = (
    "patient_id",
    "payer_id",
    "billing_provider_id",
    "claim_frequency_code",
    "original_claim_id",
    "diagnosis_codes",
)


def parse_diagnosis_codes(value: str | None) -> list[dict[str, str | int]]:
    """Parse ordered ``SYSTEM:CODE`` tokens from the controlled CSV contract."""
    diagnoses: list[dict[str, str | int]] = []
    tokens = filter(None, (part.strip() for part in (value or "").split("|")))
    for sequence, token in enumerate(tokens, start=1):
        system, separator, code = token.partition(":")
        if not separator or not system.strip() or not code.strip():
            raise ValueError(f"Invalid diagnosis token: {token}")
        diagnoses.append({"sequence": sequence, "code_system": system.strip(), "code": code.strip()})
    return diagnoses


def _validate_optional_entity(
    row: dict[str, str],
    identifier: str,
    dependent_fields: tuple[str, ...],
) -> list[str]:
    if row.get(identifier):
        return []
    return [f"MISSING_{identifier.upper()}" for field in dependent_fields if row.get(field)]


def validate_claim_row(row: dict[str, str]) -> list[str]:
    errors = [f"MISSING_{column.upper()}" for column in REQUIRED_COLUMNS if not row.get(column)]
    if row.get("service_date"):
        try:
            date.fromisoformat(row["service_date"])
        except ValueError:
            errors.append("INVALID_SERVICE_DATE")
    amounts: dict[str, Decimal] = {}
    for field in BASE_AMOUNT_FIELDS:
        if not row.get(field):
            continue
        try:
            amount = Decimal(row.get(field, ""))
            if not amount.is_finite():
                raise InvalidOperation
            amounts[field] = amount
        except InvalidOperation:
            errors.append(f"INVALID_{field.upper()}")
    for field in OPTIONAL_AMOUNT_FIELDS:
        raw_value = row.get(field, "") or "0"
        try:
            amount = Decimal(raw_value)
            if not amount.is_finite():
                raise InvalidOperation
            amounts[field] = amount
        except InvalidOperation:
            errors.append(f"INVALID_{field.upper()}")

    for field, amount in amounts.items():
        if amount < 0:
            errors.append(f"NEGATIVE_{field.upper()}")

    if all(field in amounts for field in BASE_AMOUNT_FIELDS) and (
        amounts["paid_amount"] > amounts["allowed_amount"]
        or amounts["allowed_amount"] > amounts["billed_amount"]
    ):
        errors.append("INVALID_FINANCIAL_HIERARCHY")
    if all(field in amounts for field in (*BASE_AMOUNT_FIELDS, "patient_responsibility_amount")):
        if amounts["paid_amount"] + amounts["patient_responsibility_amount"] > amounts["allowed_amount"]:
            errors.append("INVALID_ALLOWED_AMOUNT_DISTRIBUTION")

    frequency_code = row.get("claim_frequency_code") or "1"
    if frequency_code not in VALID_FREQUENCY_CODES:
        errors.append("INVALID_CLAIM_FREQUENCY_CODE")
    original_claim_id = row.get("original_claim_id")
    if frequency_code in ADJUSTMENT_FREQUENCY_CODES and not original_claim_id:
        errors.append("MISSING_ORIGINAL_CLAIM_ID")
    if frequency_code == "1" and original_claim_id:
        errors.append("UNEXPECTED_ORIGINAL_CLAIM_ID")
    if original_claim_id and original_claim_id == row.get("claim_id"):
        errors.append("SELF_REFERENTIAL_ORIGINAL_CLAIM_ID")

    adjustment_amount = amounts.get("adjustment_amount", Decimal("0"))
    if "billed_amount" in amounts and adjustment_amount > amounts["billed_amount"]:
        errors.append("INVALID_ADJUSTMENT_AMOUNT")
    adjustment_group = row.get("adjustment_group_code")
    adjustment_reason = row.get("adjustment_reason_code")
    if adjustment_amount > 0 and (not adjustment_group or not adjustment_reason):
        errors.append("INCOMPLETE_ADJUSTMENT_REASON")
    if adjustment_amount == 0 and (adjustment_group or adjustment_reason):
        errors.append("ADJUSTMENT_REASON_WITHOUT_AMOUNT")

    errors.extend(_validate_optional_entity(row, "payer_id", ("payer_name",)))
    errors.extend(
        _validate_optional_entity(
            row,
            "billing_provider_id",
            ("billing_provider_npi", "billing_provider_name"),
        )
    )
    errors.extend(
        _validate_optional_entity(
            row,
            "rendering_provider_id",
            ("rendering_provider_npi", "rendering_provider_name"),
        )
    )
    for field in ("billing_provider_npi", "rendering_provider_npi"):
        if row.get(field) and not NPI_PATTERN.fullmatch(row[field]):
            errors.append(f"INVALID_{field.upper()}")

    procedure_system = row.get("procedure_code_system")
    procedure_code = row.get("procedure_code")
    if bool(procedure_system) != bool(procedure_code):
        errors.append("INCOMPLETE_PROCEDURE_CODE")
    try:
        diagnoses = parse_diagnosis_codes(row.get("diagnosis_codes"))
        diagnosis_keys = [(diagnosis["code_system"], diagnosis["code"]) for diagnosis in diagnoses]
        if len(diagnosis_keys) != len(set(diagnosis_keys)):
            errors.append("DUPLICATE_DIAGNOSIS_CODE")
    except ValueError:
        errors.append("INVALID_DIAGNOSIS_CODE")
    return list(dict.fromkeys(errors))


def validate_claim_rows(rows: list[dict[str, str]]) -> list[tuple[dict[str, str], list[str]]]:
    """Validate rows and enforce attributes repeated at the claim-header grain."""
    header_signatures: dict[str, set[tuple[str, ...]]] = {}
    for row in rows:
        claim_id = row.get("claim_id")
        if not claim_id:
            continue
        signature = tuple(
            (row.get(field) or ("1" if field == "claim_frequency_code" else "")).strip()
            for field in CLAIM_HEADER_FIELDS
        )
        header_signatures.setdefault(claim_id, set()).add(signature)

    inconsistent_claims = {
        claim_id
        for claim_id, signatures in header_signatures.items()
        if len(signatures) > 1
    }
    validated = []
    for row in rows:
        errors = validate_claim_row(row)
        if row.get("claim_id") in inconsistent_claims:
            errors.append("INCONSISTENT_CLAIM_HEADER_ATTRIBUTES")
        validated.append((row, errors))
    return validated


def iter_validated_claim_rows(path: Path) -> Iterator[tuple[dict[str, str], list[str]]]:
    """Yield the controlled file with both row- and claim-grain validation."""
    yield from validate_claim_rows(list(iter_claim_rows(path)))


def iter_claim_rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="") as handle:
        yield from csv.DictReader(handle)
