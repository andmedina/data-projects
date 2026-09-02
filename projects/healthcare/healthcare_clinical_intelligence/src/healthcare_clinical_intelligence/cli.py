from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analytics import (
    clinical_activity_from_accepted,
    ed_utilization_from_accepted,
    eligible_ed_utilization_from_accepted,
)
from .dashboard import export_dashboard_bundle, validate_dashboard_bundle
from .fhir_client import publish_bundle
from .ml import export_readmission_cohort
from .modeling import train_readmission_baseline
from .performance import database_performance_report
from .pipeline import run_claims_file, run_fhir_file, run_hl7_file
from .postgres import (
    apply_database_migration,
    database_operational_report,
    database_quality_report,
    load_claims_csv,
    load_core_and_report,
    load_fhir_incremental,
    load_fhir_payload,
    load_hl7_file,
    open_connection,
    refresh_omop_subset,
    run_claims_database_pipeline,
    run_fhir_database_pipeline,
)
from .quality import run_quality_gate
from .synthetic import generate_fhir_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Healthcare Clinical Intelligence local runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    fhir = subparsers.add_parser("fhir-file", help="Process a synthetic FHIR Bundle JSON file")
    fhir.add_argument("input", type=Path)
    fhir.add_argument("--output", type=Path, default=Path("output"))
    claims = subparsers.add_parser("claims-file", help="Validate a synthetic claims CSV file")
    claims.add_argument("input", type=Path)
    claims.add_argument("--output", type=Path, default=Path("output"))
    hl7 = subparsers.add_parser("hl7-file", help="Parse a synthetic HL7 v2 file")
    hl7.add_argument("input", type=Path)
    hl7.add_argument("--output", type=Path, default=Path("output"))
    generate = subparsers.add_parser("generate-synthetic", help="Generate a deterministic synthetic FHIR Bundle")
    generate.add_argument("--patients", type=int, default=25)
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--output", type=Path, default=Path("data/synthetic/fhir_bundle.json"))
    ed = subparsers.add_parser("ed-utilization", help="Export monthly ED utilization from accepted FHIR records")
    ed.add_argument("accepted_input", type=Path)
    ed.add_argument("--output", type=Path, default=Path("output/ed_utilization_monthly.csv"))
    eligible_ed = subparsers.add_parser(
        "eligible-ed-utilization",
        help="Export payer-specific ED encounters per 1,000 active-coverage member months",
    )
    eligible_ed.add_argument("accepted_input", type=Path)
    eligible_ed.add_argument(
        "--output",
        type=Path,
        default=Path("output/ed_utilization_eligible_monthly.csv"),
    )
    clinical = subparsers.add_parser(
        "clinical-activity", help="Export monthly condition, procedure, and medication activity"
    )
    clinical.add_argument("accepted_input", type=Path)
    clinical.add_argument("--output", type=Path, default=Path("output/clinical_activity_monthly.csv"))
    cohort = subparsers.add_parser("readmission-cohort", help="Build a temporally valid synthetic readmission cohort")
    cohort.add_argument("accepted_input", type=Path)
    cohort.add_argument("--output", type=Path, default=Path("output/readmission_cohort.csv"))
    model = subparsers.add_parser(
        "train-readmission-baseline", help="Train a chronological logistic-regression readmission baseline"
    )
    model.add_argument("cohort_input", type=Path)
    model.add_argument("--output", type=Path, default=Path("output/readmission_baseline_report.json"))
    model.add_argument(
        "--fail-on-governance",
        action="store_true",
        help="Return exit code 1 unless the model passes synthetic-demo approval policy",
    )
    postgres = subparsers.add_parser("fhir-postgres", help="Load a FHIR Bundle JSON file into PostgreSQL raw storage")
    postgres.add_argument("input", type=Path)
    postgres.add_argument("--dsn", required=True, help="PostgreSQL connection string")
    postgres.add_argument("--source-system", default="synthea")
    claims_postgres = subparsers.add_parser(
        "claims-postgres", help="Load validated claim-line CSV data into PostgreSQL raw storage"
    )
    claims_postgres.add_argument("input", type=Path)
    claims_postgres.add_argument("--dsn", required=True)
    claims_postgres.add_argument("--source-system", default="synthetic_claims")
    claims_pipeline = subparsers.add_parser(
        "claims-pipeline", help="Load claims CSV and build canonical claim/claim-line tables"
    )
    claims_pipeline.add_argument("input", type=Path)
    claims_pipeline.add_argument("--dsn", required=True)
    claims_pipeline.add_argument("--sql-root", type=Path, default=Path("sql"))
    claims_pipeline.add_argument("--source-system", default="synthetic_claims")
    hl7_postgres = subparsers.add_parser(
        "hl7-postgres",
        help="Load controlled HL7 messages and map ADT events, ORM orders, and ORU results",
    )
    hl7_postgres.add_argument("input", type=Path)
    hl7_postgres.add_argument("--dsn", required=True)
    hl7_postgres.add_argument("--source-system", default="synthetic_hl7")
    incremental = subparsers.add_parser(
        "fhir-incremental", help="Fetch one FHIR resource type from an API using a saved checkpoint"
    )
    incremental.add_argument("resource_type", choices=["Patient", "Encounter", "Observation"])
    incremental.add_argument("--base-url", required=True)
    incremental.add_argument("--dsn", required=True)
    incremental.add_argument("--source-system", default="hapi_fhir")
    publish = subparsers.add_parser("fhir-publish", help="Upsert a synthetic FHIR Bundle to a FHIR REST server")
    publish.add_argument("input", type=Path)
    publish.add_argument("--base-url", required=True)
    pipeline = subparsers.add_parser("fhir-pipeline", help="Load FHIR, build core entities, and report quality")
    pipeline.add_argument("input", type=Path)
    pipeline.add_argument("--dsn", required=True)
    pipeline.add_argument("--sql-root", type=Path, default=Path("sql"))
    pipeline.add_argument("--source-system", default="synthea")
    migrate = subparsers.add_parser("db-migrate", help="Apply the database initialization SQL")
    migrate.add_argument("--dsn", required=True)
    migrate.add_argument("--sql-file", type=Path, default=Path("sql/000_init.sql"))
    core = subparsers.add_parser("core-load", help="Run idempotent staging-to-core transformations and quality checks")
    core.add_argument("--dsn", required=True)
    core.add_argument("--sql-root", type=Path, default=Path("sql"))
    omop = subparsers.add_parser(
        "omop-refresh", help="Refresh stable OMOP subset identifiers and reconciliation counts"
    )
    omop.add_argument("--dsn", required=True)
    omop.add_argument("--sql-root", type=Path, default=Path("sql"))
    quality = subparsers.add_parser("quality-report", help="Return core data-quality summary counts")
    quality.add_argument("--dsn", required=True)
    dashboard = subparsers.add_parser(
        "dashboard-export", help="Export dashboard-ready PostgreSQL datasets and a refresh manifest"
    )
    dashboard.add_argument("--dsn", required=True)
    dashboard.add_argument("--output", type=Path, default=Path("output/dashboard"))
    dashboard.add_argument("--model-report", type=Path)
    dashboard_validate = subparsers.add_parser(
        "dashboard-validate", help="Validate an exported dashboard bundle contract"
    )
    dashboard_validate.add_argument("input", type=Path)
    operations = subparsers.add_parser(
        "operations-report", help="Report migration state and PostgreSQL pipeline health"
    )
    operations.add_argument("--dsn", required=True)
    performance = subparsers.add_parser(
        "performance-report", help="Verify required indexes and benchmark representative marts"
    )
    performance.add_argument("--dsn", required=True)
    performance.add_argument("--maximum-query-ms", type=float, default=5000.0)
    quality_gate = subparsers.add_parser(
        "quality-gate", help="Persist quality results and fail on threshold violations"
    )
    quality_gate.add_argument("--dsn", required=True)
    quality_gate.add_argument("--pipeline-run-id")
    quality_gate.add_argument("--triggered-by", default="cli")
    quality_gate.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()
    if args.command == "fhir-file":
        print(json.dumps(run_fhir_file(args.input, args.output), indent=2))
    elif args.command == "claims-file":
        print(json.dumps(run_claims_file(args.input, args.output), indent=2))
    elif args.command == "hl7-file":
        print(json.dumps(run_hl7_file(args.input, args.output), indent=2))
    elif args.command == "generate-synthetic":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        bundle = generate_fhir_bundle(args.patients, args.seed)
        args.output.write_text(json.dumps(bundle, indent=2) + "\n")
        print(json.dumps({"output": str(args.output), "resources": len(bundle["entry"]), "patients": args.patients}))
    elif args.command == "ed-utilization":
        rows = ed_utilization_from_accepted(args.accepted_input, args.output)
        print(json.dumps({"output": str(args.output), "rows": len(rows)}, indent=2))
    elif args.command == "eligible-ed-utilization":
        rows = eligible_ed_utilization_from_accepted(args.accepted_input, args.output)
        print(json.dumps({"output": str(args.output), "rows": len(rows)}, indent=2))
    elif args.command == "clinical-activity":
        rows = clinical_activity_from_accepted(args.accepted_input, args.output)
        print(json.dumps({"output": str(args.output), "rows": len(rows)}, indent=2))
    elif args.command == "readmission-cohort":
        rows = export_readmission_cohort(args.accepted_input, args.output)
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "rows": len(rows),
                    "outcomes": sum(row["readmitted_within_30_days"] for row in rows),
                },
                indent=2,
            )
        )
    elif args.command == "train-readmission-baseline":
        report = train_readmission_baseline(args.cohort_input, args.output)
        print(json.dumps(report, indent=2))
        if args.fail_on_governance and report["approval"]["status"] != "approved_for_synthetic_demonstration":
            raise SystemExit(1)
    elif args.command == "fhir-postgres":
        with open_connection(args.dsn) as connection:
            print(
                json.dumps(
                    load_fhir_payload(connection, json.loads(args.input.read_text()), args.source_system), indent=2
                )
            )
    elif args.command == "claims-postgres":
        with open_connection(args.dsn) as connection:
            print(json.dumps(load_claims_csv(connection, args.input, args.source_system), indent=2))
    elif args.command == "claims-pipeline":
        with open_connection(args.dsn) as connection:
            print(
                json.dumps(
                    run_claims_database_pipeline(connection, args.input, args.sql_root, args.source_system), indent=2
                )
            )
    elif args.command == "hl7-postgres":
        with open_connection(args.dsn) as connection:
            print(json.dumps(load_hl7_file(connection, args.input, args.source_system), indent=2))
    elif args.command == "fhir-incremental":
        with open_connection(args.dsn) as connection:
            print(
                json.dumps(
                    load_fhir_incremental(connection, args.base_url, args.resource_type, args.source_system), indent=2
                )
            )
    elif args.command == "fhir-publish":
        published = publish_bundle(args.base_url, json.loads(args.input.read_text()))
        print(json.dumps({"base_url": args.base_url, "published": published}, indent=2))
    elif args.command == "fhir-pipeline":
        with open_connection(args.dsn) as connection:
            print(
                json.dumps(
                    run_fhir_database_pipeline(
                        connection, json.loads(args.input.read_text()), args.sql_root, args.source_system
                    ),
                    indent=2,
                )
            )
    elif args.command == "db-migrate":
        with open_connection(args.dsn) as connection:
            print(json.dumps(apply_database_migration(connection, args.sql_file), indent=2))
    elif args.command == "core-load":
        with open_connection(args.dsn) as connection:
            print(json.dumps(load_core_and_report(connection, args.sql_root), indent=2))
    elif args.command == "omop-refresh":
        with open_connection(args.dsn) as connection:
            print(json.dumps({"domains": refresh_omop_subset(connection, args.sql_root)}, indent=2))
    elif args.command == "quality-report":
        with open_connection(args.dsn) as connection:
            print(json.dumps(database_quality_report(connection), indent=2))
    elif args.command == "dashboard-export":
        with open_connection(args.dsn) as connection:
            print(json.dumps(export_dashboard_bundle(connection, args.output, args.model_report), indent=2))
    elif args.command == "dashboard-validate":
        report = validate_dashboard_bundle(args.input)
        print(json.dumps(report, indent=2))
        if report["status"] != "valid":
            raise SystemExit(1)
    elif args.command == "operations-report":
        with open_connection(args.dsn) as connection:
            print(json.dumps(database_operational_report(connection), indent=2))
    elif args.command == "performance-report":
        with open_connection(args.dsn) as connection:
            report = database_performance_report(connection, args.maximum_query_ms)
        print(json.dumps(report, indent=2))
        if report["status"] != "passed":
            raise SystemExit(1)
    elif args.command == "quality-gate":
        with open_connection(args.dsn) as connection:
            report = run_quality_gate(connection, args.triggered_by, args.pipeline_run_id, args.fail_on_warning)
        print(json.dumps(report, indent=2))
        if report["status"] == "failed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
