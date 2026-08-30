from pathlib import Path

from healthcare_clinical_intelligence.analytics import clinical_activity_from_accepted, ed_utilization_from_accepted
from healthcare_clinical_intelligence.pipeline import run_fhir_file
from healthcare_clinical_intelligence.synthetic import generate_fhir_bundle


def test_generator_is_deterministic():
    bundle = generate_fhir_bundle(3, 7)
    assert bundle == generate_fhir_bundle(3, 7)
    assert len(bundle["entry"]) >= 9
    lab_observations = [
        entry["resource"] for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == "Observation"
    ]
    assert lab_observations
    assert all(observation["category"][0]["coding"][0]["code"] == "laboratory" for observation in lab_observations)


def test_ed_export_from_sample_bundle(tmp_path: Path):
    run_fhir_file(Path("data/samples/fhir_bundle.json"), tmp_path)
    rows = ed_utilization_from_accepted(tmp_path / "accepted.jsonl", tmp_path / "ed.csv")
    assert rows == [{"reporting_month": "2025-01", "ed_encounters": 1, "patients_with_ed_encounter": 1}]


def test_clinical_activity_export_from_generated_bundle(tmp_path: Path):
    source = tmp_path / "bundle.json"
    source.write_text(__import__("json").dumps(generate_fhir_bundle(3, 4)))
    run_fhir_file(source, tmp_path / "run")
    rows = clinical_activity_from_accepted(tmp_path / "run" / "accepted.jsonl", tmp_path / "clinical.csv")
    assert rows
    assert sum(row["conditions"] for row in rows) > 0
