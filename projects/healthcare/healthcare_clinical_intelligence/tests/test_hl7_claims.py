from pathlib import Path

from healthcare_clinical_intelligence.claims import parse_diagnosis_codes, validate_claim_row, validate_claim_rows
from healthcare_clinical_intelligence.hl7 import parse_message
from healthcare_clinical_intelligence.pipeline import run_claims_file, run_hl7_file


def test_adt_message_extracts_patient():
    message = Path("data/samples/adt_a01.hl7").read_text()
    parsed = parse_message(message)
    assert parsed["message_type"] == "ADT^A01"
    assert parsed["patient_id"] == "p-001"
    assert parsed["encounter_event"]["encounter_id"] == "e-001"
    assert parsed["encounter_event"]["event_state"] == "admitted"
    assert not parsed["errors"]


def test_oru_message_extracts_observation():
    parsed = parse_message(Path("data/samples/oru_r01.hl7").read_text())
    assert parsed["message_type"] == "ORU^R01"
    assert parsed["observations"][0]["code"] == "8310-5"
    assert parsed["observations"][0]["value"] == "37.1"


def test_adt_lifecycle_extracts_ordered_state_changes():
    messages = Path("data/samples/adt_lifecycle.hl7").read_text().strip().split("\n\n")
    events = [parse_message(message)["encounter_event"] for message in messages]

    assert [event["event_state"] for event in events] == [
        "admitted",
        "transferred",
        "discharged",
    ]
    assert events[1]["prior_location"] == "WARD^101^1"
    assert events[1]["assigned_location"] == "WARD^202^1"


def test_orm_message_extracts_order_context():
    parsed = parse_message(Path("data/samples/orm_o01.hl7").read_text())

    assert not parsed["errors"]
    assert parsed["message_type"] == "ORM^O01"
    assert parsed["orders"] == [
        {
            "order_id": "order-001",
            "order_control": "NW",
            "order_status": "SC",
            "code": "71046",
            "code_display": "Chest radiograph",
            "code_system": "CPT",
            "ordered_at": "2025-01-03T11:15:00",
            "encounter_id": "e-001",
        }
    ]


def test_unsupported_hl7_profile_is_rejected():
    unsupported = Path("data/samples/adt_a01.hl7").read_text().replace("ADT^A01", "ADT^A04")

    assert "UNSUPPORTED_MESSAGE_TYPE" in parse_message(unsupported)["errors"]


def test_controlled_hl7_profile_fields_are_required():
    transfer = Path("data/samples/adt_lifecycle.hl7").read_text().strip().split("\n\n")[1]
    invalid_transfer = transfer.replace("WARD^101^1", "")
    invalid_order = Path("data/samples/orm_o01.hl7").read_text().replace("ORC|NW", "ORC|ZZ")

    assert "MISSING_PRIOR_LOCATION" in parse_message(invalid_transfer)["errors"]
    assert "INVALID_ORDER_CONTROL" in parse_message(invalid_order)["errors"]


def test_claim_financial_hierarchy_is_validated():
    row = {
        "claim_id": "c1",
        "claim_line_id": "l1",
        "patient_id": "p1",
        "service_date": "2025-01-01",
        "billed_amount": "10",
        "allowed_amount": "11",
        "paid_amount": "9",
    }
    assert "INVALID_FINANCIAL_HIERARCHY" in validate_claim_row(row)


def test_expanded_claim_adjustment_contract_is_validated():
    row = {
        "claim_id": "c2",
        "claim_line_id": "l2",
        "patient_id": "p1",
        "service_date": "2025-01-01",
        "claim_frequency_code": "7",
        "billed_amount": "100",
        "allowed_amount": "80",
        "paid_amount": "70",
        "patient_responsibility_amount": "20",
        "adjustment_amount": "20",
        "billing_provider_npi": "not-an-npi",
        "procedure_code_system": "CPT",
    }

    errors = validate_claim_row(row)

    assert "MISSING_ORIGINAL_CLAIM_ID" in errors
    assert "INVALID_ALLOWED_AMOUNT_DISTRIBUTION" in errors
    assert "INCOMPLETE_ADJUSTMENT_REASON" in errors
    assert "MISSING_BILLING_PROVIDER_ID" in errors
    assert "INVALID_BILLING_PROVIDER_NPI" in errors
    assert "INCOMPLETE_PROCEDURE_CODE" in errors


def test_ordered_diagnosis_codes_are_normalized():
    assert parse_diagnosis_codes("ICD10CM:E11.9|ICD10CM:I10") == [
        {"sequence": 1, "code_system": "ICD10CM", "code": "E11.9"},
        {"sequence": 2, "code_system": "ICD10CM", "code": "I10"},
    ]
    assert "INVALID_DIAGNOSIS_CODE" in validate_claim_row(
        {
            "claim_id": "c1",
            "claim_line_id": "l1",
            "patient_id": "p1",
            "service_date": "2025-01-01",
            "billed_amount": "10",
            "allowed_amount": "10",
            "paid_amount": "10",
            "diagnosis_codes": "missing-system-separator",
        }
    )


def test_claim_header_attributes_must_agree_across_lines():
    first = {
        "claim_id": "c1",
        "claim_line_id": "l1",
        "patient_id": "p1",
        "service_date": "2025-01-01",
        "payer_id": "payer-a",
        "billed_amount": "10",
        "allowed_amount": "10",
        "paid_amount": "10",
    }
    second = {**first, "claim_line_id": "l2", "payer_id": "payer-b"}

    validated = validate_claim_rows([first, second])

    assert all("INCONSISTENT_CLAIM_HEADER_ATTRIBUTES" in errors for _, errors in validated)


def test_claim_service_date_must_be_iso_date():
    errors = validate_claim_row(
        {
            "claim_id": "c1",
            "claim_line_id": "l1",
            "patient_id": "p1",
            "service_date": "01/31/2025",
            "billed_amount": "10",
            "allowed_amount": "10",
            "paid_amount": "10",
        }
    )

    assert "INVALID_SERVICE_DATE" in errors


def test_claims_and_hl7_file_runners_write_reports(tmp_path: Path):
    assert run_claims_file(Path("data/samples/claims.csv"), tmp_path)["accepted"] == 1
    assert run_hl7_file(Path("data/samples/adt_a01.hl7"), tmp_path)["accepted"] == 1


def test_hl7_lifecycle_file_runner_accepts_all_events(tmp_path: Path):
    assert run_hl7_file(Path("data/samples/adt_lifecycle.hl7"), tmp_path) == {
        "source_records": 3,
        "accepted": 3,
        "rejected": 0,
    }


def test_expanded_claim_file_passes_controlled_contract(tmp_path: Path):
    report = run_claims_file(Path("data/samples/claims_expanded.csv"), tmp_path)

    assert report == {"source_records": 3, "accepted": 3, "rejected": 0}


def test_claim_sql_contract_loads_latest_versions_and_dimensions():
    staging_sql = Path("sql/staging/010_staging_views.sql").read_text()
    load_sql = Path("sql/core/022_load_claims.sql").read_text()
    mart_sql = Path("sql/marts/031_claims_cost.sql").read_text()

    assert "source_version_rank = 1" in staging_sql
    assert "insert into core.payer" in load_sql
    assert "insert into core.claim_diagnosis" in load_sql
    assert "insert into core.claim_line_procedure" in load_sql
    assert "insert into core.claim_line_adjustment" in load_sql
    assert "successor.original_claim_id = claim.claim_id" in mart_sql
    assert "claim.claim_frequency_code <> '8'" in mart_sql


def test_hl7_sql_contract_persists_lifecycle_and_order_events():
    core_sql = Path("sql/core/020_core_schema.sql").read_text()
    mart_sql = Path("sql/marts/034_hl7_operational.sql").read_text()

    assert "core.hl7_encounter_event" in core_sql
    assert "core.hl7_order_event" in core_sql
    assert "mart.hl7_encounter_current_state" in mart_sql
    assert "mart.hl7_order_current_state" in mart_sql
    assert "where event_code <> 'A08'" in mart_sql
    assert "order by event_at desc" in mart_sql
