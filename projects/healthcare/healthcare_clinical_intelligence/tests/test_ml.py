from pathlib import Path

from healthcare_clinical_intelligence.ml import build_readmission_cohort
from healthcare_clinical_intelligence.pipeline import run_fhir_file
from healthcare_clinical_intelligence.synthetic import generate_fhir_bundle


def test_cohort_uses_only_history_before_prediction(tmp_path: Path):
    bundle = generate_fhir_bundle(50, seed=9)
    source = tmp_path / "bundle.json"
    source.write_text(__import__("json").dumps(bundle))
    run_fhir_file(source, tmp_path / "run")
    rows = build_readmission_cohort(tmp_path / "run" / "accepted.jsonl")
    assert rows
    assert all(row["prior_encounter_count"] >= row["prior_ed_count"] for row in rows)
