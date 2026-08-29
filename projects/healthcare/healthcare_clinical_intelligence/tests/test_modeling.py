import csv
from pathlib import Path

import pytest

from healthcare_clinical_intelligence.modeling import train_readmission_baseline


def test_baseline_model_writes_report(tmp_path: Path):
    pytest.importorskip("sklearn")
    cohort = tmp_path / "cohort.csv"
    fields = ["index_encounter_id", "patient_id", "prediction_at", "prior_encounter_count", "prior_ed_count", "age_at_prediction", "readmitted_within_30_days"]
    rows = [
        {"index_encounter_id": f"e-{index}", "patient_id": f"p-{index}", "prediction_at": f"2025-01-{index + 1:02d}T00:00:00Z", "prior_encounter_count": index % 4, "prior_ed_count": index % 2, "age_at_prediction": 30 + index, "readmitted_within_30_days": int(index in {1, 5, 9, 11})}
        for index in range(12)
    ]
    with cohort.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report = train_readmission_baseline(cohort, tmp_path / "report.json")
    assert report["model"] == "logistic_regression"
    assert (tmp_path / "report.json").exists()
