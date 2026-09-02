#!/usr/bin/env python3
"""Run the complete synthetic platform path against PostgreSQL."""

from __future__ import annotations

import argparse
import json
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from healthcare_clinical_intelligence.dashboard import export_dashboard_bundle, validate_dashboard_bundle
from healthcare_clinical_intelligence.ml import export_readmission_cohort
from healthcare_clinical_intelligence.modeling import train_readmission_baseline
from healthcare_clinical_intelligence.performance import database_performance_report
from healthcare_clinical_intelligence.pipeline import run_fhir_file
from healthcare_clinical_intelligence.postgres import (
    apply_database_migration,
    database_operational_report,
    load_hl7_file,
    open_connection,
    run_claims_database_pipeline,
    run_fhir_database_pipeline,
)
from healthcare_clinical_intelligence.quality import run_quality_gate
from healthcare_clinical_intelligence.synthetic import generate_fhir_bundle

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


@contextmanager
def _ephemeral_database(base_dsn: str) -> Iterator[str]:
    try:
        import psycopg
        from psycopg import sql
        from psycopg.conninfo import conninfo_to_dict, make_conninfo
    except ModuleNotFoundError as exc:
        raise RuntimeError("PostgreSQL smoke testing requires: pip install -e '.[postgres]'") from exc

    database_name = f"hci_smoke_{uuid.uuid4().hex[:12]}"
    base_parameters = conninfo_to_dict(base_dsn)
    admin_parameters = {**base_parameters, "dbname": "postgres"}
    admin_dsn = make_conninfo("", **admin_parameters)
    with psycopg.connect(admin_dsn, autocommit=True) as connection:
        connection.execute(sql.SQL("create database {}").format(sql.Identifier(database_name)))

    target_dsn = make_conninfo("", **{**base_parameters, "dbname": database_name})
    try:
        yield target_dsn
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as connection:
            connection.execute(
                "select pg_terminate_backend(pid) from pg_stat_activity where datname=%s and pid <> pg_backend_pid()",
                (database_name,),
            )
            connection.execute(sql.SQL("drop database {}").format(sql.Identifier(database_name)))


def run_smoke_test(dsn: str) -> dict[str, object]:
    sql_root = PROJECT_ROOT / "sql"
    with TemporaryDirectory(prefix="hci-postgres-smoke-") as temporary_directory:
        work_dir = Path(temporary_directory)
        database_bundle = generate_fhir_bundle(patient_count=40, seed=42)
        model_bundle_path = work_dir / "model_bundle.json"
        model_bundle_path.write_text(json.dumps(generate_fhir_bundle(patient_count=250, seed=42)))

        with open_connection(dsn) as connection:
            first_migration = apply_database_migration(connection, sql_root / "000_init.sql")
            second_migration = apply_database_migration(connection, sql_root / "000_init.sql")
            _require(second_migration["status"] == "already_current", "second migration was not idempotent")

            fhir = run_fhir_database_pipeline(connection, database_bundle, sql_root, "ci_fhir")
            _require(fhir["ingestion"]["rejected"] == 0, "generated FHIR bundle was rejected")
            fixture_fhir = run_fhir_database_pipeline(
                connection,
                json.loads((PROJECT_ROOT / "data/samples/fhir_bundle.json").read_text()),
                sql_root,
                "ci_fixture",
            )
            _require(fixture_fhir["ingestion"]["loaded"] == 3, "controlled FHIR fixture did not load")
            claims = run_claims_database_pipeline(
                connection,
                PROJECT_ROOT / "data/samples/claims_expanded.csv",
                sql_root,
                "ci_claims",
            )
            _require(claims["ingestion"]["rejected"] == 0, "controlled claims fixture was rejected")

            hl7_reports = [
                load_hl7_file(connection, PROJECT_ROOT / fixture, "ci_hl7")
                for fixture in (
                    "data/samples/adt_lifecycle.hl7",
                    "data/samples/orm_o01.hl7",
                    "data/samples/oru_r01.hl7",
                )
            ]
            _require(all(report["rejected"] == 0 for report in hl7_reports), "controlled HL7 fixture was rejected")

            model_run = work_dir / "model_run"
            run_fhir_file(model_bundle_path, model_run)
            cohort_path = work_dir / "readmission_cohort.csv"
            export_readmission_cohort(model_run / "accepted.jsonl", cohort_path)
            model_report_path = work_dir / "readmission_baseline_report.json"
            train_readmission_baseline(cohort_path, model_report_path)

            quality = run_quality_gate(connection, triggered_by="postgres-smoke")
            _require(quality["failures"] == 0, "quality gate returned blocking failures")

            dashboard_dir = work_dir / "dashboard"
            manifest = export_dashboard_bundle(connection, dashboard_dir, model_report_path)
            contract = validate_dashboard_bundle(dashboard_dir)
            _require(contract["status"] == "valid", f"dashboard contract failed: {contract['errors']}")

            performance = database_performance_report(connection)
            _require(performance["status"] == "passed", "performance smoke test failed")

            duplicate_fhir = run_fhir_database_pipeline(connection, database_bundle, sql_root, "ci_fhir")
            duplicate_claims = run_claims_database_pipeline(
                connection,
                PROJECT_ROOT / "data/samples/claims_expanded.csv",
                sql_root,
                "ci_claims",
            )
            duplicate_hl7 = [
                load_hl7_file(connection, PROJECT_ROOT / fixture, "ci_hl7")
                for fixture in (
                    "data/samples/adt_lifecycle.hl7",
                    "data/samples/orm_o01.hl7",
                    "data/samples/oru_r01.hl7",
                )
            ]
            _require(duplicate_fhir["ingestion"]["loaded"] == 0, "FHIR rerun inserted duplicate raw rows")
            _require(duplicate_claims["ingestion"]["loaded"] == 0, "claims rerun inserted duplicate raw rows")
            _require(all(report["loaded"] == 0 for report in duplicate_hl7), "HL7 rerun inserted duplicate raw rows")

            final_quality = run_quality_gate(connection, triggered_by="postgres-smoke-idempotency")
            _require(final_quality["failures"] == 0, "post-rerun quality gate returned blocking failures")
            operations = database_operational_report(connection)
            _require(operations["running"] == 0, "completed smoke test left running pipelines")
            _require(operations["stale"] == 0, "completed smoke test left stale pipelines")
            _require(operations["missing_completion"] == 0, "terminal pipeline is missing completion metadata")
            _require(operations["count_mismatches"] == 0, "pipeline counts do not reconcile")

        return {
            "status": "passed",
            "migration": first_migration,
            "fhir_resources": fhir["ingestion"]["source_records"],
            "claims_lines": claims["ingestion"]["source_records"],
            "hl7_messages": sum(int(report["source_messages"]) for report in hl7_reports),
            "quality_checks": final_quality["checks"],
            "quality_warnings": final_quality["warnings"],
            "dashboard_datasets": len(manifest["datasets"]),
            "dashboard_contract": contract["status"],
            "performance_benchmarks": len(performance["benchmarks"]),
            "pipeline_types": len(operations["latest_success"]),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", required=True, help="Base PostgreSQL connection string")
    parser.add_argument(
        "--ephemeral",
        action="store_true",
        help="Create and remove a uniquely named temporary database for the test",
    )
    args = parser.parse_args()
    if args.ephemeral:
        with _ephemeral_database(args.dsn) as ephemeral_dsn:
            report = run_smoke_test(ephemeral_dsn)
    else:
        report = run_smoke_test(args.dsn)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
