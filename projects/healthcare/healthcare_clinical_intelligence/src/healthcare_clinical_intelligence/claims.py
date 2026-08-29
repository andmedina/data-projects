"""Controlled CSV claims validation for the later payer integration."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import csv
from pathlib import Path
from typing import Iterator

REQUIRED_COLUMNS = {"claim_id", "claim_line_id", "patient_id", "service_date", "billed_amount", "allowed_amount", "paid_amount"}


def validate_claim_row(row: dict[str, str]) -> list[str]:
    errors = [f"MISSING_{column.upper()}" for column in REQUIRED_COLUMNS if not row.get(column)]
    amounts: dict[str, Decimal] = {}
    for field in ("billed_amount", "allowed_amount", "paid_amount"):
        try:
            amounts[field] = Decimal(row.get(field, ""))
        except InvalidOperation:
            errors.append(f"INVALID_{field.upper()}")
    if len(amounts) == 3 and (amounts["paid_amount"] > amounts["allowed_amount"] or amounts["allowed_amount"] > amounts["billed_amount"]):
        errors.append("INVALID_FINANCIAL_HIERARCHY")
    return errors


def iter_claim_rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="") as handle:
        yield from csv.DictReader(handle)
