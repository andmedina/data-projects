"""Reproducible baseline modeling for the synthetic readmission cohort."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

FEATURES = ["prior_encounter_count", "prior_ed_count", "age_at_prediction"]
TARGET = "readmitted_within_30_days"


def train_readmission_baseline(cohort_path: Path, output_path: Path) -> dict[str, Any]:
    """Train a chronological logistic-regression baseline and write a compact report."""
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import average_precision_score, roc_auc_score
    except ModuleNotFoundError as exc:
        raise RuntimeError("ML support requires: pip install -e '.[ml]'") from exc
    with cohort_path.open() as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: row["prediction_at"])
    if len(rows) < 10:
        raise ValueError("At least 10 cohort rows are required for a baseline model")
    split = max(1, int(len(rows) * 0.8))
    train, test = rows[:split], rows[split:]
    x_train = [[float(row[field] or 0) for field in FEATURES] for row in train]
    y_train = [int(row[TARGET]) for row in train]
    x_test = [[float(row[field] or 0) for field in FEATURES] for row in test]
    y_test = [int(row[TARGET]) for row in test]
    if len(set(y_train)) < 2 or len(set(y_test)) < 2:
        raise ValueError("Chronological train and test partitions must each contain both outcome classes")
    model = LogisticRegression(max_iter=1_000, class_weight="balanced", random_state=42)
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    report = {
        "model": "logistic_regression",
        "features": FEATURES,
        "target": TARGET,
        "train_rows": len(train),
        "test_rows": len(test),
        "train_prevalence": round(sum(y_train) / len(y_train), 4),
        "test_prevalence": round(sum(y_test) / len(y_test), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "pr_auc": round(float(average_precision_score(y_test, probabilities)), 4),
        "coefficients": {feature: round(float(coefficient), 6) for feature, coefficient in zip(FEATURES, model.coef_[0], strict=True)},
        "limitations": "Synthetic-data engineering demonstration only; not clinically validated or deployable.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    return report
