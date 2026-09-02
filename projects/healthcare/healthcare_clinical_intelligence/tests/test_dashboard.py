from __future__ import annotations

import csv
import json
from pathlib import Path

from healthcare_clinical_intelligence.dashboard import (
    DASHBOARD_CONTRACT_VERSION,
    EXPORT_QUERIES,
    export_dashboard_bundle,
    validate_dashboard_bundle,
)


class FakeCursor:
    def __init__(self, results: list[tuple[list[str], list[tuple[object, ...]]]]) -> None:
        self.results = results
        self.description: list[tuple[str]] = []
        self.rows: list[tuple[object, ...]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str) -> None:
        columns, self.rows = self.results.pop(0)
        self.description = [(column,) for column in columns]

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.rows


class FakeConnection:
    def __init__(self) -> None:
        self.results = [(["metric", "value"], [(name, index)]) for index, name in enumerate(EXPORT_QUERIES, start=1)]

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.results)


def test_dashboard_bundle_writes_all_datasets_and_manifest(tmp_path: Path) -> None:
    model_report = tmp_path / "model.json"
    model_report.write_text('{"roc_auc": 0.6}\n')

    manifest = export_dashboard_bundle(FakeConnection(), tmp_path / "dashboard", model_report)

    assert len(manifest["datasets"]) == len(EXPORT_QUERIES)
    assert all(dataset["rows"] == 1 for dataset in manifest["datasets"])
    assert all(len(dataset["sha256"]) == 64 for dataset in manifest["datasets"])
    assert manifest["contract_version"] == DASHBOARD_CONTRACT_VERSION
    assert manifest["model_report"] == "readmission_baseline_report.json"
    assert json.loads((tmp_path / "dashboard" / "manifest.json").read_text())["source"].startswith("PostgreSQL")
    with (tmp_path / "dashboard" / "executive_overview.csv").open(newline="") as handle:
        assert list(csv.reader(handle)) == [["metric", "value"], ["executive_overview", "1"]]
    assert validate_dashboard_bundle(tmp_path / "dashboard")["status"] == "valid"


def test_dashboard_contract_detects_tampered_dataset(tmp_path: Path) -> None:
    export_dashboard_bundle(FakeConnection(), tmp_path / "dashboard")
    (tmp_path / "dashboard" / "executive_overview.csv").write_text("metric,value\ntampered,999\n")

    report = validate_dashboard_bundle(tmp_path / "dashboard")

    assert report["status"] == "invalid"
    assert any("executive_overview" in error and "checksum" in error for error in report["errors"])


def test_dashboard_contract_rejects_unsafe_file_path(tmp_path: Path) -> None:
    export_dashboard_bundle(FakeConnection(), tmp_path / "dashboard")
    manifest_path = tmp_path / "dashboard" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["datasets"][0]["file"] = "../outside.csv"
    manifest_path.write_text(json.dumps(manifest))

    report = validate_dashboard_bundle(tmp_path / "dashboard")

    assert report["status"] == "invalid"
    assert any("unsafe" in error for error in report["errors"])


def test_dashboard_claim_queries_use_current_adjudication_state() -> None:
    assert "successor.original_claim_id = claim.claim_id" in EXPORT_QUERIES["executive_overview"]
    assert "patient_responsibility_amount" in EXPORT_QUERIES["claim_cost_monthly"]
    assert "adjustment_amount" in EXPORT_QUERIES["claim_cost_monthly"]


def test_dashboard_includes_hl7_current_state_contracts() -> None:
    assert "hl7_encounter_current_state" in EXPORT_QUERIES
    assert "hl7_order_current_state" in EXPORT_QUERIES
    assert "latest_event_at" in EXPORT_QUERIES["hl7_order_current_state"]


def test_dashboard_includes_eligibility_aware_population_health_contracts() -> None:
    assert "member_eligibility_monthly" in EXPORT_QUERIES
    assert "ed_utilization_eligible_monthly" in EXPORT_QUERIES
    assert "ed_encounters_per_1000_member_months" in EXPORT_QUERIES["ed_utilization_eligible_monthly"]


def test_dashboard_includes_omop_reconciliation_and_vocabulary_status() -> None:
    assert "omop_domain_row_count" in EXPORT_QUERIES
    assert "omop_vocabulary_status" in EXPORT_QUERIES
    assert "source_rows - omop_rows" in EXPORT_QUERIES["omop_domain_row_count"]
    assert "mapped_to_standard" in EXPORT_QUERIES["omop_vocabulary_status"]


def test_dashboard_includes_imaging_activity_contract() -> None:
    assert "imaging_activity_monthly" in EXPORT_QUERIES
    assert "imaging_instances" in EXPORT_QUERIES["imaging_activity_monthly"]


def test_dashboard_exports_governed_model_datasets_and_artifacts(tmp_path: Path) -> None:
    report = {
        "experiment_id": "exp-001",
        "train_rows": 80,
        "test_rows": 20,
        "split": {"patient_overlap_count": 0, "temporal_overlap": False, "excluded_crossover_rows": 2},
        "roc_auc": 0.7,
        "pr_auc": 0.4,
        "calibration": {
            "brier_score": 0.2,
            "expected_calibration_error": 0.1,
            "bins": [{"lower_bound": 0, "upper_bound": 0.2, "rows": 3}],
        },
        "subgroup_performance": [{"dimension": "age_group", "group": "under_45", "rows": 10}],
        "approval": {
            "status": "approved_for_synthetic_demonstration",
            "clinical_use_approved": False,
            "checks": [{"check": "minimum_test_rows", "observed": 20, "threshold": 20, "passed": True}],
        },
        "artifacts": {
            "predictions": "predictions.csv",
            "model_card": "model_card.md",
            "experiment_registry": "registry.jsonl",
        },
    }
    report_path = tmp_path / "model_report.json"
    report_path.write_text(json.dumps(report))
    (tmp_path / "predictions.csv").write_text("patient_id,prediction\np1,0.2\n")
    (tmp_path / "model_card.md").write_text("# Model card\n")
    (tmp_path / "registry.jsonl").write_text('{"experiment_id":"exp-001"}\n')

    manifest = export_dashboard_bundle(FakeConnection(), tmp_path / "dashboard", report_path)

    dataset_names = {dataset["name"] for dataset in manifest["datasets"]}
    assert {
        "model_governance",
        "model_calibration",
        "model_subgroup_performance",
        "model_approval_checks",
    } <= dataset_names
    assert len(manifest["model_artifacts"]) == 3
    assert (tmp_path / "dashboard" / "model_governance.csv").exists()
