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


def test_runner_writes_audit_outputs(tmp_path: Path):
    sample = Path("data/samples/fhir_bundle.json")
    report = run_fhir_file(sample, tmp_path)
    assert report == {"source_records": 4, "accepted": 3, "rejected": 1}
    assert len((tmp_path / "accepted.jsonl").read_text().splitlines()) == 3
    assert json.loads((tmp_path / "run_report.json").read_text())["rejected"] == 1
