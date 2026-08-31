"""Reproducible dashboard extracts from the PostgreSQL analytics model."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPORT_QUERIES = {
    "executive_overview": """
        select
            (select count(*) from core.patient) as patients,
            (select count(*) from core.encounter) as encounters,
            (select count(*) from core.encounter where encounter_class = 'EMER'
                and encounter_status in ('finished', 'completed')) as ed_encounters,
            (select count(*) from core.observation) as observations,
            (select count(*) from core.observation where category_code = 'laboratory') as laboratory_observations,
            (select count(*) from core.condition_occurrence) as conditions,
            (select count(*) from core.procedure_occurrence) as procedures,
            (select count(*) from core.medication_request) as medication_requests,
            (select count(*) from core.claim claim
                where claim.claim_frequency_code <> '8'
                  and not exists (
                      select 1 from core.claim successor
                      where successor.original_claim_id = claim.claim_id
                  )) as claims,
            (select coalesce(sum(claim.paid_amount), 0) from core.claim claim
                where claim.claim_frequency_code <> '8'
                  and not exists (
                      select 1 from core.claim successor
                      where successor.original_claim_id = claim.claim_id
                  )) as total_paid_amount,
            ((select count(*) from quarantine.fhir_resource)
                + (select count(*) from quarantine.claim_line)
                + (select count(*) from quarantine.hl7_message)) as quarantined_records
    """,
    "ed_utilization_monthly": """
        select reporting_month, ed_encounters, patients_with_ed_encounter,
               ed_encounters_per_patient
        from mart.ed_utilization_monthly
        order by reporting_month
    """,
    "clinical_activity_monthly": """
        select reporting_month, patients_with_activity, conditions, procedures,
               medication_requests, total_clinical_activities
        from mart.clinical_activity_monthly
        order by reporting_month
    """,
    "claim_cost_monthly": """
        select reporting_month, claims, claim_lines, billed_amount, allowed_amount,
               paid_amount, unpaid_amount, patient_responsibility_amount,
               adjustment_amount
        from mart.claim_cost_monthly
        order by reporting_month
    """,
    "lab_result_completeness_monthly": """
        select reporting_month, final_laboratory_observations, observations_with_result,
               observations_with_absent_reason, observations_missing_result,
               result_completeness_percent
        from mart.lab_result_completeness_monthly
        order by reporting_month
    """,
    "data_quality": """
        select qr.quality_run_id::text, qr.check_name, qr.quality_dimension,
               qr.severity, qr.observed_value, qr.failure_threshold,
               qr.status, qr.evaluated_at
        from operational.quality_result qr
        where qr.quality_run_id = (
            select quality_run_id
            from operational.quality_run
            where completed_at is not null
            order by completed_at desc
            limit 1
        )
        order by qr.check_name
    """,
    "pipeline_runs": """
        select run_id::text, pipeline_name, source_description, status,
               started_at, completed_at,
               case when completed_at is not null
                    then round(extract(epoch from completed_at - started_at)::numeric, 3)
               end as duration_seconds
        from operational.pipeline_run
        order by started_at desc
        limit 100
    """,
}


def _column_name(column: Any) -> str:
    if hasattr(column, "name"):
        return str(column.name)
    return str(column[0])


def _export_query(connection: Any, query: str, output_path: Path) -> int:
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [_column_name(column) for column in cursor.description]
        rows = cursor.fetchall()
    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def export_dashboard_bundle(
    connection: Any,
    output_dir: Path,
    model_report_path: Path | None = None,
) -> dict[str, Any]:
    """Export versionable CSV shapes plus a manifest for dashboard refreshes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    datasets = []
    for name, query in EXPORT_QUERIES.items():
        output_path = output_dir / f"{name}.csv"
        row_count = _export_query(connection, query, output_path)
        datasets.append({"name": name, "file": output_path.name, "rows": row_count})

    manifest: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "PostgreSQL canonical and mart layers",
        "datasets": datasets,
    }
    if model_report_path is not None:
        report = json.loads(model_report_path.read_text())
        copied_report = output_dir / "readmission_baseline_report.json"
        copied_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        manifest["model_report"] = copied_report.name

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
