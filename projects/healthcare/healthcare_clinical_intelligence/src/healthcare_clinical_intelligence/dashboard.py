"""Reproducible dashboard extracts from the PostgreSQL analytics model."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DASHBOARD_CONTRACT_VERSION = "1.0.0"


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
    "member_eligibility_monthly": """
        select reporting_month, payer_organization_id, member_months
        from mart.member_eligibility_monthly
        order by reporting_month, payer_organization_id
    """,
    "ed_utilization_eligible_monthly": """
        select reporting_month, payer_organization_id, member_months,
               ed_encounters, patients_with_ed_encounter,
               ed_encounters_per_1000_member_months
        from mart.ed_utilization_eligible_monthly
        order by reporting_month, payer_organization_id
    """,
    "omop_domain_row_count": """
        select domain_name, source_rows, omop_rows,
               source_rows - omop_rows as row_difference
        from omop.domain_row_count
        order by domain_name
    """,
    "omop_vocabulary_status": """
        select domain_id, source_vocabulary, source_code, target_concept_id,
               source_rows, mapped_to_standard
        from omop.source_to_standard_concept_status
        order by domain_id, source_vocabulary, source_code
    """,
    "imaging_activity_monthly": """
        select reporting_month, imaging_studies, patients_with_imaging,
               imaging_series, imaging_instances, distinct_modalities
        from mart.imaging_activity_monthly
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
    "hl7_encounter_current_state": """
        select encounter_id, patient_id, current_state, patient_class,
               current_location, latest_event_at, admitted_at, discharged_at,
               lifecycle_events
        from mart.hl7_encounter_current_state
        order by latest_event_at desc, encounter_id
    """,
    "hl7_order_current_state": """
        select order_id, patient_id, encounter_id, order_control, order_status,
               code_system, code, code_display, ordered_at, latest_event_at,
               message_control_id
        from mart.hl7_order_current_state
        order by ordered_at desc, order_id
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
               records_seen, records_loaded, records_duplicates, records_rejected,
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _dataset_metadata(name: str, output_path: Path, rows: int, columns: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "file": output_path.name,
        "rows": rows,
        "columns": columns,
        "bytes": output_path.stat().st_size,
        "sha256": _sha256(output_path),
    }


def _export_query(connection: Any, query: str, output_path: Path) -> tuple[int, list[str]]:
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [_column_name(column) for column in cursor.description]
        rows = cursor.fetchall()
    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows), columns


def _write_dict_dataset(output_path: Path, rows: list[dict[str, Any]]) -> tuple[int, list[str]]:
    if not rows:
        output_path.write_text("")
        return 0, []
    columns = list(rows[0])
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows), columns


def _export_model_governance(report: dict[str, Any], output_dir: Path) -> list[dict[str, Any]]:
    if not {"experiment_id", "approval", "calibration", "subgroup_performance"} <= report.keys():
        return []
    datasets = {
        "model_governance": [
            {
                "experiment_id": report["experiment_id"],
                "approval_status": report["approval"]["status"],
                "clinical_use_approved": report["approval"]["clinical_use_approved"],
                "train_rows": report["train_rows"],
                "test_rows": report["test_rows"],
                "patient_overlap_count": report["split"]["patient_overlap_count"],
                "temporal_overlap": report["split"].get("temporal_overlap"),
                "excluded_crossover_rows": report["split"].get("excluded_crossover_rows", 0),
                "roc_auc": report["roc_auc"],
                "pr_auc": report["pr_auc"],
                "brier_score": report["calibration"]["brier_score"],
                "expected_calibration_error": report["calibration"]["expected_calibration_error"],
            }
        ],
        "model_calibration": report["calibration"]["bins"],
        "model_subgroup_performance": report["subgroup_performance"],
        "model_approval_checks": report["approval"]["checks"],
    }
    exported = []
    for name, rows in datasets.items():
        output_path = output_dir / f"{name}.csv"
        row_count, columns = _write_dict_dataset(output_path, rows)
        exported.append(_dataset_metadata(name, output_path, row_count, columns))
    return exported


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
        row_count, columns = _export_query(connection, query, output_path)
        datasets.append(_dataset_metadata(name, output_path, row_count, columns))

    manifest: dict[str, Any] = {
        "contract_version": DASHBOARD_CONTRACT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "PostgreSQL canonical and mart layers",
        "datasets": datasets,
    }
    if model_report_path is not None:
        report = json.loads(model_report_path.read_text())
        copied_report = output_dir / "readmission_baseline_report.json"
        copied_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        manifest["model_report"] = copied_report.name
        manifest["model_report_sha256"] = _sha256(copied_report)
        manifest["datasets"].extend(_export_model_governance(report, output_dir))
        copied_artifacts = []
        for artifact_type in ("predictions", "model_card", "experiment_registry"):
            artifact_name = report.get("artifacts", {}).get(artifact_type)
            if not artifact_name:
                continue
            source_path = model_report_path.parent / Path(artifact_name).name
            if source_path.exists():
                destination = output_dir / source_path.name
                if source_path.resolve() != destination.resolve():
                    shutil.copyfile(source_path, destination)
                copied_artifacts.append(
                    {
                        "type": artifact_type,
                        "file": destination.name,
                        "bytes": destination.stat().st_size,
                        "sha256": _sha256(destination),
                    }
                )
        if copied_artifacts:
            manifest["model_artifacts"] = copied_artifacts

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def validate_dashboard_bundle(output_dir: Path) -> dict[str, Any]:
    """Validate dashboard files against their manifest without external dependencies."""
    errors: list[str] = []
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.is_file():
        return {"status": "invalid", "datasets": 0, "errors": ["manifest.json is missing"]}

    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "datasets": 0, "errors": [f"manifest.json is unreadable: {exc}"]}

    if manifest.get("contract_version") != DASHBOARD_CONTRACT_VERSION:
        errors.append(
            f"contract_version must be {DASHBOARD_CONTRACT_VERSION}; found {manifest.get('contract_version')!r}"
        )
    datasets = manifest.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        return {"status": "invalid", "datasets": 0, "errors": errors + ["datasets must be a non-empty list"]}

    names: set[str] = set()
    for position, dataset in enumerate(datasets):
        if not isinstance(dataset, dict):
            errors.append(f"dataset {position} must be an object")
            continue
        name = dataset.get("name")
        file_name = dataset.get("file")
        if not isinstance(name, str) or not name:
            errors.append(f"dataset {position} has no valid name")
        elif name in names:
            errors.append(f"dataset name {name!r} is duplicated")
        else:
            names.add(name)
        if not isinstance(file_name, str) or not file_name or Path(file_name).name != file_name:
            errors.append(f"dataset {name!r} has an unsafe or missing file name")
            continue
        data_path = output_dir / file_name
        if not data_path.is_file():
            errors.append(f"dataset {name!r} file {file_name!r} is missing")
            continue
        with data_path.open(newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            actual_rows = sum(1 for _ in reader)
        if dataset.get("columns") != header:
            errors.append(f"dataset {name!r} columns do not match the manifest")
        if dataset.get("rows") != actual_rows:
            errors.append(f"dataset {name!r} row count does not match the manifest")
        if dataset.get("bytes") != data_path.stat().st_size:
            errors.append(f"dataset {name!r} byte count does not match the manifest")
        if dataset.get("sha256") != _sha256(data_path):
            errors.append(f"dataset {name!r} checksum does not match the manifest")

    model_report = manifest.get("model_report")
    if model_report is not None:
        if not isinstance(model_report, str) or Path(model_report).name != model_report:
            errors.append("model_report has an unsafe file name")
        else:
            report_path = output_dir / model_report
            if not report_path.is_file():
                errors.append("model_report file is missing")
            elif manifest.get("model_report_sha256") != _sha256(report_path):
                errors.append("model_report checksum does not match the manifest")

    for artifact in manifest.get("model_artifacts", []):
        if not isinstance(artifact, dict):
            errors.append("model artifact metadata must be an object")
            continue
        file_name = artifact.get("file")
        if not isinstance(file_name, str) or Path(file_name).name != file_name:
            errors.append("model artifact has an unsafe file name")
            continue
        artifact_path = output_dir / file_name
        if not artifact_path.is_file():
            errors.append(f"model artifact {file_name!r} is missing")
        else:
            if artifact.get("bytes") != artifact_path.stat().st_size:
                errors.append(f"model artifact {file_name!r} byte count does not match the manifest")
            if artifact.get("sha256") != _sha256(artifact_path):
                errors.append(f"model artifact {file_name!r} checksum does not match the manifest")

    return {"status": "valid" if not errors else "invalid", "datasets": len(datasets), "errors": errors}
