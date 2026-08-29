from pathlib import Path

from healthcare_clinical_intelligence.analytics import ed_utilization_from_accepted
from healthcare_clinical_intelligence.pipeline import run_fhir_file
from healthcare_clinical_intelligence.synthetic import generate_fhir_bundle


def test_generator_is_deterministic():
    assert generate_fhir_bundle(3, 7) == generate_fhir_bundle(3, 7)
    assert len(generate_fhir_bundle(3, 7)["entry"]) >= 9


def test_ed_export_from_sample_bundle(tmp_path: Path):
    run_fhir_file(Path("data/samples/fhir_bundle.json"), tmp_path)
    rows = ed_utilization_from_accepted(tmp_path / "accepted.jsonl", tmp_path / "ed.csv")
    assert rows == [{"reporting_month": "2025-01", "ed_encounters": 1, "patients_with_ed_encounter": 1}]
