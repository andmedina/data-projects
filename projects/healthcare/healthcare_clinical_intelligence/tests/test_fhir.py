import json
from pathlib import Path

from healthcare_clinical_intelligence.fhir import normalize_resource, reference_id, validate_resource
from healthcare_clinical_intelligence.pipeline import run_fhir_file


def test_reference_and_encounter_normalization():
    encounter = {"resourceType": "Encounter", "id": "e1", "subject": {"reference": "https://example.org/fhir/Patient/p1"}, "status": "finished"}
    assert reference_id(encounter["subject"]["reference"]) == "p1"
    assert normalize_resource(encounter)["patient_id"] == "p1"


def test_observation_without_subject_is_rejected():
    assert "MISSING_OBSERVATION_SUBJECT" in validate_resource({"resourceType": "Observation", "id": "o1", "status": "final"})


def test_observation_quantity_and_units_are_normalized():
    observation = {
        "resourceType": "Observation",
        "id": "lab-1",
        "status": "final",
        "subject": {"reference": "Patient/p1"},
        "category": [{"coding": [{"system": "category-system", "code": "laboratory"}]}],
        "code": {"coding": [{"system": "http://loinc.org", "code": "718-7"}]},
        "valueQuantity": {"value": 13.4, "unit": "g/dL", "system": "http://unitsofmeasure.org", "code": "g/dL"},
    }

    canonical = normalize_resource(observation)

    assert canonical["category"]["code"] == "laboratory"
    assert canonical["value_type"] == "Quantity"
    assert canonical["value_numeric"] == 13.4
    assert canonical["unit_code"] == "g/dL"


def test_observation_rejects_multiple_choice_values():
    observation = {
        "resourceType": "Observation", "id": "lab-2", "status": "final",
        "subject": {"reference": "Patient/p1"}, "valueString": "positive", "valueBoolean": True,
    }

    assert "MULTIPLE_OBSERVATION_VALUES" in validate_resource(observation)


def test_observation_rejects_unsupported_value_type():
    observation = {
        "resourceType": "Observation", "id": "lab-3", "status": "final",
        "subject": {"reference": "Patient/p1"}, "valueRange": {"low": {"value": 1}, "high": {"value": 2}},
    }

    assert "UNSUPPORTED_OBSERVATION_VALUE_TYPE" in validate_resource(observation)


def test_coverage_requires_a_valid_period_and_normalizes_boundaries():
    coverage = {
        "resourceType": "Coverage",
        "id": "cov-1",
        "status": "active",
        "beneficiary": {"reference": "Patient/p1"},
        "payor": [{"reference": "Organization/payer-1"}],
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
    }

    assert validate_resource(coverage) == []
    assert normalize_resource(coverage) == {
        "resource_type": "Coverage",
        "source_resource_id": "cov-1",
        "patient_id": "p1",
        "payer_id": "payer-1",
        "status": "active",
        "coverage_start": "2025-01-01",
        "coverage_end": "2025-12-31",
    }

    coverage["period"] = {"start": "2025-12-31", "end": "2025-01-01"}
    assert "INVALID_COVERAGE_PERIOD" in validate_resource(coverage)


def test_coverage_missing_period_boundaries_is_rejected():
    coverage = {
        "resourceType": "Coverage",
        "id": "cov-2",
        "status": "active",
        "beneficiary": {"reference": "Patient/p1"},
        "period": {},
    }

    errors = validate_resource(coverage)

    assert "MISSING_COVERAGE_PERIOD_START" in errors
    assert "MISSING_COVERAGE_PERIOD_END" in errors
    assert "MISSING_COVERAGE_PAYOR" in errors


def test_lab_incident_fixtures_show_missing_then_corrected_value(tmp_path: Path):
    missing_dir = tmp_path / "missing"
    corrected_dir = tmp_path / "corrected"

    assert run_fhir_file(Path("data/samples/fhir_lab_incident_missing.json"), missing_dir)["accepted"] == 3
    assert run_fhir_file(Path("data/samples/fhir_lab_incident_corrected.json"), corrected_dir)["accepted"] == 3

    missing_rows = [json.loads(line)["canonical"] for line in (missing_dir / "accepted.jsonl").read_text().splitlines()]
    corrected_rows = [json.loads(line)["canonical"] for line in (corrected_dir / "accepted.jsonl").read_text().splitlines()]
    missing_lab = next(row for row in missing_rows if row["resource_type"] == "Observation")
    corrected_lab = next(row for row in corrected_rows if row["resource_type"] == "Observation")

    assert missing_lab["category"]["code"] == "laboratory"
    assert missing_lab["value_type"] is None
    assert corrected_lab["value_numeric"] == 13.4
    assert corrected_lab["unit_code"] == "g/dL"


def test_runner_writes_audit_outputs(tmp_path: Path):
    sample = Path("data/samples/fhir_bundle.json")
    report = run_fhir_file(sample, tmp_path)
    assert report == {"source_records": 4, "accepted": 3, "rejected": 1}
    assert len((tmp_path / "accepted.jsonl").read_text().splitlines()) == 3
    assert json.loads((tmp_path / "run_report.json").read_text())["rejected"] == 1
