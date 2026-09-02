import csv
from pathlib import Path

import pytest

from healthcare_clinical_intelligence.modeling import evaluate_model_approval, train_readmission_baseline


def test_baseline_model_writes_report(tmp_path: Path):
    pytest.importorskip("sklearn")
    cohort = tmp_path / "cohort.csv"
    fields = [
        "index_encounter_id",
        "patient_id",
        "prediction_at",
        "prior_encounter_count",
        "prior_ed_count",
        "age_at_prediction",
        "readmitted_within_30_days",
    ]
    rows = [
        {
            "index_encounter_id": f"e-{index}",
            "patient_id": f"p-{index // 2}",
            "prediction_at": f"2025-01-{index + 1:02d}T00:00:00Z",
            "prior_encounter_count": index % 4,
            "prior_ed_count": index % 2,
            "age_at_prediction": 30 + index,
            "readmitted_within_30_days": int(index in {1, 5, 9, 11}),
        }
        for index in range(12)
    ]
    with cohort.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report = train_readmission_baseline(cohort, tmp_path / "report.json")

    assert report["model"] == "logistic_regression"
    assert report["split"]["patient_overlap_count"] == 0
    assert report["split"]["temporal_overlap"] is False
    assert report["split"]["excluded_crossover_rows"] == 2
    assert report["calibration"]["bins"]
    assert report["subgroup_performance"]
    assert report["approval"]["clinical_use_approved"] is False
    assert report["approval"]["status"] == "review_required"
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "report_predictions.csv").exists()
    assert (
        "Clinical use, patient-level intervention, and deployment are prohibited"
        in (tmp_path / "report_model_card.md").read_text()
    )

    repeat = train_readmission_baseline(cohort, tmp_path / "report.json")

    assert repeat["experiment_id"] == report["experiment_id"]
    assert len((tmp_path / "model_experiment_registry.jsonl").read_text().splitlines()) == 1


def test_technical_approval_never_grants_clinical_use(tmp_path: Path):
    pytest.importorskip("sklearn")
    cohort = tmp_path / "cohort.csv"
    fields = [
        "index_encounter_id",
        "patient_id",
        "prediction_at",
        "prior_encounter_count",
        "prior_ed_count",
        "age_at_prediction",
        "readmitted_within_30_days",
    ]
    rows = [
        {
            "index_encounter_id": f"e-{index}",
            "patient_id": f"p-{index}",
            "prediction_at": f"2025-01-{index + 1:02d}T00:00:00Z",
            "prior_encounter_count": index % 3,
            "prior_ed_count": index % 2,
            "age_at_prediction": 50 + index,
            "readmitted_within_30_days": index % 2,
        }
        for index in range(12)
    ]
    with cohort.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report = train_readmission_baseline(cohort, tmp_path / "report.json")
    permissive_policy = {
        "minimum_test_rows": 1,
        "minimum_roc_auc": 0,
        "maximum_brier_score": 1,
        "maximum_expected_calibration_error": 1,
        "minimum_subgroup_review_rows": 1,
        "minimum_reviewed_subgroups": 1,
        "maximum_subgroup_brier_score": 1,
        "maximum_excluded_crossover_fraction": 1,
    }

    approval = evaluate_model_approval(report, permissive_policy)

    assert approval["status"] == "approved_for_synthetic_demonstration"
    assert approval["clinical_use_approved"] is False
