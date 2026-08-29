from pathlib import Path

from healthcare_clinical_intelligence.claims import validate_claim_row
from healthcare_clinical_intelligence.hl7 import parse_message
from healthcare_clinical_intelligence.pipeline import run_claims_file, run_hl7_file


def test_adt_message_extracts_patient():
    message = Path("data/samples/adt_a01.hl7").read_text()
    parsed = parse_message(message)
    assert parsed["message_type"] == "ADT^A01"
    assert parsed["patient_id"] == "p-001"
    assert not parsed["errors"]


def test_oru_message_extracts_observation():
    parsed = parse_message(Path("data/samples/oru_r01.hl7").read_text())
    assert parsed["message_type"] == "ORU^R01"
    assert parsed["observations"][0]["code"] == "8310-5"
    assert parsed["observations"][0]["value"] == "37.1"


def test_claim_financial_hierarchy_is_validated():
    row = {"claim_id": "c1", "claim_line_id": "l1", "patient_id": "p1", "service_date": "2025-01-01", "billed_amount": "10", "allowed_amount": "11", "paid_amount": "9"}
    assert "INVALID_FINANCIAL_HIERARCHY" in validate_claim_row(row)


def test_claims_and_hl7_file_runners_write_reports(tmp_path: Path):
    assert run_claims_file(Path("data/samples/claims.csv"), tmp_path)["accepted"] == 1
    assert run_hl7_file(Path("data/samples/adt_a01.hl7"), tmp_path)["accepted"] == 1
