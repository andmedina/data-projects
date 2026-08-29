from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_claims_file, run_fhir_file, run_hl7_file
from .postgres import database_quality_report, execute_sql_file, load_core_and_report, load_fhir_incremental, load_fhir_payload, open_connection, run_fhir_database_pipeline
from .synthetic import generate_fhir_bundle
from .analytics import ed_utilization_from_accepted
from .ml import export_readmission_cohort
from .fhir_client import publish_bundle


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
    cohort = subparsers.add_parser("readmission-cohort", help="Build a temporally valid synthetic readmission cohort")
    cohort.add_argument("accepted_input", type=Path)
    cohort.add_argument("--output", type=Path, default=Path("output/readmission_cohort.csv"))
    postgres = subparsers.add_parser("fhir-postgres", help="Load a FHIR Bundle JSON file into PostgreSQL raw storage")
    postgres.add_argument("input", type=Path)
    postgres.add_argument("--dsn", required=True, help="PostgreSQL connection string")
    postgres.add_argument("--source-system", default="synthea")
    incremental = subparsers.add_parser("fhir-incremental", help="Fetch one FHIR resource type from an API using a saved checkpoint")
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
    quality = subparsers.add_parser("quality-report", help="Return core data-quality summary counts")
    quality.add_argument("--dsn", required=True)
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
    elif args.command == "readmission-cohort":
        rows = export_readmission_cohort(args.accepted_input, args.output)
        print(json.dumps({"output": str(args.output), "rows": len(rows), "outcomes": sum(row["readmitted_within_30_days"] for row in rows)}, indent=2))
    elif args.command == "fhir-postgres":
        with open_connection(args.dsn) as connection:
            print(json.dumps(load_fhir_payload(connection, json.loads(args.input.read_text()), args.source_system), indent=2))
    elif args.command == "fhir-incremental":
        with open_connection(args.dsn) as connection:
            print(json.dumps(load_fhir_incremental(connection, args.base_url, args.resource_type, args.source_system), indent=2))
    elif args.command == "fhir-publish":
        published = publish_bundle(args.base_url, json.loads(args.input.read_text()))
        print(json.dumps({"base_url": args.base_url, "published": published}, indent=2))
    elif args.command == "fhir-pipeline":
        with open_connection(args.dsn) as connection:
            print(json.dumps(run_fhir_database_pipeline(connection, json.loads(args.input.read_text()), args.sql_root, args.source_system), indent=2))
    elif args.command == "db-migrate":
        with open_connection(args.dsn) as connection:
            execute_sql_file(connection, args.sql_file)
            print(json.dumps({"applied": str(args.sql_file)}))
    elif args.command == "core-load":
        with open_connection(args.dsn) as connection:
            print(json.dumps(load_core_and_report(connection, args.sql_root), indent=2))
    elif args.command == "quality-report":
        with open_connection(args.dsn) as connection:
            print(json.dumps(database_quality_report(connection), indent=2))


if __name__ == "__main__":
    main()
