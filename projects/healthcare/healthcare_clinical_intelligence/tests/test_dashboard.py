from __future__ import annotations

import csv
import json
from pathlib import Path

from healthcare_clinical_intelligence.dashboard import EXPORT_QUERIES, export_dashboard_bundle


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
    assert manifest["model_report"] == "readmission_baseline_report.json"
    assert json.loads((tmp_path / "dashboard" / "manifest.json").read_text())["source"].startswith("PostgreSQL")
    with (tmp_path / "dashboard" / "executive_overview.csv").open(newline="") as handle:
        assert list(csv.reader(handle)) == [["metric", "value"], ["executive_overview", "1"]]
