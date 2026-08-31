"""Reproducible modeling and governance for the synthetic readmission cohort."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
from typing import Any


FEATURES = ["prior_encounter_count", "prior_ed_count", "age_at_prediction"]
TARGET = "readmitted_within_30_days"
MODEL_CONFIG = {
    "implementation_version": "readmission-governance-v1",
    "model": "logistic_regression",
    "class_weight": "balanced",
    "max_iter": 1_000,
    "random_state": 42,
    "train_fraction": 0.8,
    "split_method": "strict_patient_level_temporal_cutoff",
    "decision_threshold": 0.5,
    "calibration_bins": 5,
}
APPROVAL_POLICY = {
    "minimum_test_rows": 20,
    "minimum_roc_auc": 0.5,
    "maximum_brier_score": 0.30,
    "maximum_expected_calibration_error": 0.25,
    "minimum_subgroup_review_rows": 5,
    "minimum_reviewed_subgroups": 2,
    "maximum_subgroup_brier_score": 0.35,
    "maximum_excluded_crossover_fraction": 0.25,
}


def _patient_temporal_split(
    rows: list[dict[str, str]],
    train_fraction: float,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], str]:
    """Apply a strict time cutoff and exclude patients crossing the boundary."""
    patient_predictions: dict[str, list[str]] = {}
    for row in rows:
        patient_predictions.setdefault(row["patient_id"], []).append(row["prediction_at"])
    if len(patient_predictions) < 2:
        raise ValueError("At least two patients are required for a patient-level split")
    ordered_predictions = sorted(row["prediction_at"] for row in rows)
    cutoff_index = min(len(ordered_predictions) - 2, max(0, int(len(rows) * train_fraction) - 1))
    cutoff_at = ordered_predictions[cutoff_index]
    train_patients = {
        patient_id
        for patient_id, predictions in patient_predictions.items()
        if max(predictions) <= cutoff_at
    }
    test_patients = {
        patient_id
        for patient_id, predictions in patient_predictions.items()
        if min(predictions) > cutoff_at
    }
    crossover_patients = set(patient_predictions) - train_patients - test_patients
    train = [row for row in rows if row["patient_id"] in train_patients]
    test = [row for row in rows if row["patient_id"] in test_patients]
    excluded = [row for row in rows if row["patient_id"] in crossover_patients]
    if not train or not test:
        raise ValueError("Strict patient-level temporal split produced an empty partition")
    return train, test, excluded, cutoff_at


def _classification_metrics(actual: list[int], probabilities: list[float], threshold: float) -> dict[str, Any]:
    predicted = [int(probability >= threshold) for probability in probabilities]
    true_positive = sum(observed == 1 and prediction == 1 for observed, prediction in zip(actual, predicted, strict=True))
    false_positive = sum(observed == 0 and prediction == 1 for observed, prediction in zip(actual, predicted, strict=True))
    false_negative = sum(observed == 1 and prediction == 0 for observed, prediction in zip(actual, predicted, strict=True))
    true_negative = sum(observed == 0 and prediction == 0 for observed, prediction in zip(actual, predicted, strict=True))
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    specificity = true_negative / (true_negative + false_positive) if true_negative + false_positive else 0.0
    return {
        "decision_threshold": threshold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "confusion_matrix": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "true_negative": true_negative,
        },
    }


def _calibration_report(actual: list[int], probabilities: list[float], bins: int) -> dict[str, Any]:
    brier_score = sum((probability - observed) ** 2 for observed, probability in zip(actual, probabilities, strict=True)) / len(actual)
    calibration_bins = []
    expected_calibration_error = 0.0
    for bin_index in range(bins):
        lower = bin_index / bins
        upper = (bin_index + 1) / bins
        members = [
            (observed, probability)
            for observed, probability in zip(actual, probabilities, strict=True)
            if lower <= probability < upper or (bin_index == bins - 1 and probability == 1.0)
        ]
        if not members:
            continue
        observed_rate = sum(observed for observed, _ in members) / len(members)
        mean_probability = sum(probability for _, probability in members) / len(members)
        absolute_gap = abs(observed_rate - mean_probability)
        expected_calibration_error += len(members) / len(actual) * absolute_gap
        calibration_bins.append(
            {
                "lower_bound": round(lower, 4),
                "upper_bound": round(upper, 4),
                "rows": len(members),
                "mean_probability": round(mean_probability, 4),
                "observed_rate": round(observed_rate, 4),
                "absolute_gap": round(absolute_gap, 4),
            }
        )
    return {
        "brier_score": round(brier_score, 4),
        "expected_calibration_error": round(expected_calibration_error, 4),
        "bins": calibration_bins,
    }


def _age_group(row: dict[str, str]) -> str:
    raw_age = row.get("age_at_prediction")
    if not raw_age:
        return "unknown"
    age = float(raw_age)
    if age < 45:
        return "under_45"
    if age < 65:
        return "45_to_64"
    return "65_and_over"


def _prior_ed_group(row: dict[str, str]) -> str:
    return "prior_ed" if float(row.get("prior_ed_count") or 0) > 0 else "no_prior_ed"


def _subgroup_report(
    rows: list[dict[str, str]],
    actual: list[int],
    probabilities: list[float],
) -> list[dict[str, Any]]:
    reviews = []
    dimensions = {
        "age_group": [_age_group(row) for row in rows],
        "prior_ed_group": [_prior_ed_group(row) for row in rows],
    }
    for dimension, values in dimensions.items():
        for group in sorted(set(values)):
            indexes = [index for index, value in enumerate(values) if value == group]
            group_actual = [actual[index] for index in indexes]
            group_probabilities = [probabilities[index] for index in indexes]
            brier_score = sum(
                (probability - observed) ** 2
                for observed, probability in zip(group_actual, group_probabilities, strict=True)
            ) / len(indexes)
            reviews.append(
                {
                    "dimension": dimension,
                    "group": group,
                    "rows": len(indexes),
                    "positives": sum(group_actual),
                    "prevalence": round(sum(group_actual) / len(indexes), 4),
                    "mean_probability": round(sum(group_probabilities) / len(indexes), 4),
                    "brier_score": round(brier_score, 4),
                }
            )
    return reviews


def evaluate_model_approval(report: dict[str, Any], policy: dict[str, float | int] | None = None) -> dict[str, Any]:
    """Evaluate technical release criteria without granting clinical approval."""
    applied_policy = policy or APPROVAL_POLICY
    reviewed_subgroups = [
        group
        for group in report["subgroup_performance"]
        if group["rows"] >= applied_policy["minimum_subgroup_review_rows"]
    ]
    worst_subgroup_brier = max((group["brier_score"] for group in reviewed_subgroups), default=0.0)
    checks = [
        {
            "check": "minimum_test_rows",
            "observed": report["test_rows"],
            "threshold": applied_policy["minimum_test_rows"],
            "passed": report["test_rows"] >= applied_policy["minimum_test_rows"],
        },
        {
            "check": "patient_overlap",
            "observed": report["split"]["patient_overlap_count"],
            "threshold": 0,
            "passed": report["split"]["patient_overlap_count"] == 0,
        },
        {
            "check": "temporal_overlap",
            "observed": report["split"]["temporal_overlap"],
            "threshold": False,
            "passed": not report["split"]["temporal_overlap"],
        },
        {
            "check": "maximum_excluded_crossover_fraction",
            "observed": report["split"]["excluded_crossover_fraction"],
            "threshold": applied_policy["maximum_excluded_crossover_fraction"],
            "passed": report["split"]["excluded_crossover_fraction"]
            <= applied_policy["maximum_excluded_crossover_fraction"],
        },
        {
            "check": "minimum_roc_auc",
            "observed": report["roc_auc"],
            "threshold": applied_policy["minimum_roc_auc"],
            "passed": report["roc_auc"] >= applied_policy["minimum_roc_auc"],
        },
        {
            "check": "maximum_brier_score",
            "observed": report["calibration"]["brier_score"],
            "threshold": applied_policy["maximum_brier_score"],
            "passed": report["calibration"]["brier_score"] <= applied_policy["maximum_brier_score"],
        },
        {
            "check": "maximum_expected_calibration_error",
            "observed": report["calibration"]["expected_calibration_error"],
            "threshold": applied_policy["maximum_expected_calibration_error"],
            "passed": report["calibration"]["expected_calibration_error"]
            <= applied_policy["maximum_expected_calibration_error"],
        },
        {
            "check": "minimum_reviewed_subgroups",
            "observed": len(reviewed_subgroups),
            "threshold": applied_policy["minimum_reviewed_subgroups"],
            "passed": len(reviewed_subgroups) >= applied_policy["minimum_reviewed_subgroups"],
        },
        {
            "check": "maximum_reviewed_subgroup_brier_score",
            "observed": worst_subgroup_brier,
            "threshold": applied_policy["maximum_subgroup_brier_score"],
            "passed": worst_subgroup_brier <= applied_policy["maximum_subgroup_brier_score"],
        },
    ]
    passed = all(check["passed"] for check in checks)
    return {
        "status": "approved_for_synthetic_demonstration" if passed else "review_required",
        "clinical_use_approved": False,
        "policy": applied_policy,
        "checks": checks,
        "limitations": "Technical approval applies only to this synthetic demonstration; clinical deployment is prohibited.",
    }


def _artifact_paths(output_path: Path) -> tuple[Path, Path, Path]:
    base_name = output_path.stem.removesuffix("_report")
    predictions_path = output_path.with_name(f"{base_name}_predictions.csv")
    model_card_path = output_path.with_name(f"{base_name}_model_card.md")
    registry_path = output_path.with_name("model_experiment_registry.jsonl")
    return predictions_path, model_card_path, registry_path


def _write_model_card(report: dict[str, Any], path: Path) -> None:
    failed_checks = [check["check"] for check in report["approval"]["checks"] if not check["passed"]]
    failed_summary = ", ".join(failed_checks) if failed_checks else "none"
    content = f"""# Synthetic Readmission Baseline Model Card

## Intended use

Engineering demonstration of a temporally ordered, patient-level 30-day readmission workflow using synthetic data. Clinical use, patient-level intervention, and deployment are prohibited.

## Experiment

- Experiment ID: `{report['experiment_id']}`
- Cohort SHA-256: `{report['cohort_sha256']}`
- Model: `{report['model']}`
- Features: {', '.join(report['features'])}
- Train/test rows: {report['train_rows']} / {report['test_rows']}
- Patient overlap: {report['split']['patient_overlap_count']}
- Temporal overlap: {report['split']['temporal_overlap']}
- Excluded crossover rows: {report['split']['excluded_crossover_rows']}

## Evaluation

- Test prevalence: {report['test_prevalence']}
- ROC-AUC: {report['roc_auc']}
- PR-AUC: {report['pr_auc']}
- Brier score: {report['calibration']['brier_score']}
- Expected calibration error: {report['calibration']['expected_calibration_error']}

## Governance

- Status: `{report['approval']['status']}`
- Clinical use approved: `false`
- Failed technical checks: {failed_summary}
- Subgroup dimensions reviewed: age group and prior ED-use group

Subgroup estimates with small row counts are unstable. Synthetic performance does not establish clinical validity, safety, fairness, or utility.
"""
    path.write_text(content)


def _append_experiment_registry(report: dict[str, Any], registry_path: Path) -> None:
    existing_ids = set()
    if registry_path.exists():
        with registry_path.open() as handle:
            existing_ids = {
                json.loads(line)["experiment_id"]
                for line in handle
                if line.strip()
            }
    if report["experiment_id"] in existing_ids:
        return
    registry_entry = {
        "experiment_id": report["experiment_id"],
        "trained_at_utc": report["trained_at_utc"],
        "cohort_sha256": report["cohort_sha256"],
        "model": report["model"],
        "roc_auc": report["roc_auc"],
        "pr_auc": report["pr_auc"],
        "brier_score": report["calibration"]["brier_score"],
        "approval_status": report["approval"]["status"],
        "report_file": report["artifacts"]["report"],
    }
    with registry_path.open("a") as handle:
        handle.write(json.dumps(registry_entry, sort_keys=True) + "\n")


def train_readmission_baseline(cohort_path: Path, output_path: Path) -> dict[str, Any]:
    """Train the baseline and write evaluation, prediction, registry, and model-card artifacts."""
    try:
        import sklearn
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import average_precision_score, roc_auc_score
    except ModuleNotFoundError as exc:
        raise RuntimeError("ML support requires: pip install -e '.[ml]'") from exc

    cohort_bytes = cohort_path.read_bytes()
    with cohort_path.open() as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: (row["prediction_at"], row["patient_id"], row["index_encounter_id"]))
    if len(rows) < 10:
        raise ValueError("At least 10 cohort rows are required for a baseline model")
    train, test, excluded, cutoff_at = _patient_temporal_split(rows, MODEL_CONFIG["train_fraction"])
    x_train = [[float(row[field] or 0) for field in FEATURES] for row in train]
    y_train = [int(row[TARGET]) for row in train]
    x_test = [[float(row[field] or 0) for field in FEATURES] for row in test]
    y_test = [int(row[TARGET]) for row in test]
    if len(set(y_train)) < 2 or len(set(y_test)) < 2:
        raise ValueError("Patient-level chronological train and test partitions must each contain both outcome classes")

    model = LogisticRegression(
        max_iter=MODEL_CONFIG["max_iter"],
        class_weight=MODEL_CONFIG["class_weight"],
        random_state=MODEL_CONFIG["random_state"],
    )
    model.fit(x_train, y_train)
    probabilities = [float(value) for value in model.predict_proba(x_test)[:, 1]]
    cohort_sha256 = hashlib.sha256(cohort_bytes).hexdigest()
    runtime = {"python": platform.python_version(), "scikit_learn": sklearn.__version__}
    experiment_payload = json.dumps(
        {
            "cohort_sha256": cohort_sha256,
            "features": FEATURES,
            "target": TARGET,
            "config": MODEL_CONFIG,
            "approval_policy": APPROVAL_POLICY,
            "runtime": runtime,
        },
        sort_keys=True,
    )
    experiment_id = hashlib.sha256(experiment_payload.encode()).hexdigest()[:16]
    train_patients = {row["patient_id"] for row in train}
    test_patients = {row["patient_id"] for row in test}
    predictions_path, model_card_path, registry_path = _artifact_paths(output_path)

    report: dict[str, Any] = {
        "experiment_id": experiment_id,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "cohort_sha256": cohort_sha256,
        "model": MODEL_CONFIG["model"],
        "features": FEATURES,
        "target": TARGET,
        "config": MODEL_CONFIG,
        "runtime": runtime,
        "train_rows": len(train),
        "test_rows": len(test),
        "train_prevalence": round(sum(y_train) / len(y_train), 4),
        "test_prevalence": round(sum(y_test) / len(y_test), 4),
        "split": {
            "method": MODEL_CONFIG["split_method"],
            "cutoff_at": cutoff_at,
            "train_patients": len(train_patients),
            "test_patients": len(test_patients),
            "patient_overlap_count": len(train_patients & test_patients),
            "train_end_at": max(row["prediction_at"] for row in train),
            "test_start_at": min(row["prediction_at"] for row in test),
            "temporal_overlap": max(row["prediction_at"] for row in train)
            >= min(row["prediction_at"] for row in test),
            "excluded_crossover_patients": len({row["patient_id"] for row in excluded}),
            "excluded_crossover_rows": len(excluded),
            "excluded_crossover_fraction": round(len(excluded) / len(rows), 4),
        },
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "pr_auc": round(float(average_precision_score(y_test, probabilities)), 4),
        "classification": _classification_metrics(y_test, probabilities, MODEL_CONFIG["decision_threshold"]),
        "calibration": _calibration_report(y_test, probabilities, MODEL_CONFIG["calibration_bins"]),
        "subgroup_performance": _subgroup_report(test, y_test, probabilities),
        "coefficients": {
            feature: round(float(coefficient), 6)
            for feature, coefficient in zip(FEATURES, model.coef_[0], strict=True)
        },
        "artifacts": {
            "report": output_path.name,
            "predictions": predictions_path.name,
            "model_card": model_card_path.name,
            "experiment_registry": registry_path.name,
        },
        "limitations": "Synthetic-data engineering demonstration only; not clinically validated or deployable.",
    }
    report["approval"] = evaluate_model_approval(report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with predictions_path.open("w", newline="") as handle:
        fields = [
            "index_encounter_id",
            "patient_id",
            "prediction_at",
            "actual_outcome",
            "predicted_probability",
            "predicted_label",
            "age_group",
            "prior_ed_group",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row, observed, probability in zip(test, y_test, probabilities, strict=True):
            writer.writerow(
                {
                    "index_encounter_id": row["index_encounter_id"],
                    "patient_id": row["patient_id"],
                    "prediction_at": row["prediction_at"],
                    "actual_outcome": observed,
                    "predicted_probability": round(probability, 8),
                    "predicted_label": int(probability >= MODEL_CONFIG["decision_threshold"]),
                    "age_group": _age_group(row),
                    "prior_ed_group": _prior_ed_group(row),
                }
            )
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    _write_model_card(report, model_card_path)
    _append_experiment_registry(report, registry_path)
    return report
