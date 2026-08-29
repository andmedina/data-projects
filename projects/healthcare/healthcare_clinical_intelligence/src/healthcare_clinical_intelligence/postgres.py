"""PostgreSQL raw-layer loader. Requires the optional ``postgres`` extra."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from pathlib import Path

from .fhir import iter_resources, validate_resource
from .fhir_client import latest_last_updated, paginated_bundles, resource_url


@contextmanager
def open_connection(dsn: str) -> Iterator[Any]:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError("PostgreSQL support requires: pip install -e '.[postgres]'") from exc
    with psycopg.connect(dsn) as connection:
        yield connection


def load_fhir_payload(connection: Any, payload: dict[str, Any], source_system: str = "synthea") -> dict[str, int | str]:
    """Persist raw FHIR JSON and quarantined invalid records in one database run."""
    run_id = str(uuid.uuid4())
    report: dict[str, int | str] = {"run_id": run_id, "source_records": 0, "loaded": 0, "duplicates": 0, "rejected": 0}
    with connection.cursor() as cursor:
        cursor.execute(
            "insert into operational.pipeline_run (run_id, pipeline_name, status, source_description) values (%s, %s, 'running', %s)",
            (run_id, "fhir_raw_ingestion", source_system),
        )
        for resource in iter_resources(payload):
            report["source_records"] += 1
            errors = validate_resource(resource)
            resource_type, resource_id = resource.get("resourceType"), resource.get("id")
            if errors:
                cursor.execute(
                    "insert into quarantine.fhir_resource (run_id, source_system, resource_type, source_resource_id, payload, reason_code, reason_detail) values (%s,%s,%s,%s,%s::jsonb,%s,%s) on conflict do nothing",
                    (run_id, source_system, resource_type, resource_id, json.dumps(resource), errors[0], ",".join(errors)),
                )
                report["rejected"] += 1
                continue
            digest = hashlib.sha256(json.dumps(resource, sort_keys=True).encode()).hexdigest()
            cursor.execute(
                """insert into raw.fhir_resource
                   (source_system, resource_type, source_resource_id, last_updated_at, payload, payload_sha256, run_id)
                   values (%s,%s,%s,%s,%s::jsonb,%s,%s)
                   on conflict (source_system, resource_type, source_resource_id, payload_sha256) do nothing
                   returning raw_resource_id""",
                (source_system, resource_type, resource_id, (resource.get("meta") or {}).get("lastUpdated"), json.dumps(resource), digest, run_id),
            )
            if cursor.fetchone():
                report["loaded"] += 1
            else:
                report["duplicates"] += 1
        status = "partial" if report["rejected"] else "succeeded"
        cursor.execute("update operational.pipeline_run set status = %s, completed_at = current_timestamp where run_id = %s", (status, run_id))
    connection.commit()
    return report


def load_fhir_incremental(
    connection: Any,
    base_url: str,
    resource_type: str,
    source_system: str = "hapi_fhir",
    fetcher: Any = None,
) -> dict[str, int | str | None]:
    """Load every page since its saved watermark, then atomically advance it."""
    pipeline_name = "fhir_raw_ingestion"
    with connection.cursor() as cursor:
        cursor.execute(
            "select watermark_at::text from operational.ingestion_checkpoint where pipeline_name=%s and source_system=%s and resource_type=%s",
            (pipeline_name, source_system, resource_type),
        )
        row = cursor.fetchone()
    since = row[0] if row else None
    report: dict[str, int | str | None] = {"resource_type": resource_type, "since": since, "source_records": 0, "loaded": 0, "duplicates": 0, "rejected": 0}
    latest: str | None = None
    initial_url = resource_url(base_url, resource_type, since)
    iterator = paginated_bundles(initial_url) if fetcher is None else paginated_bundles(initial_url, fetcher)
    for bundle in iterator:
        page_report = load_fhir_payload(connection, bundle, source_system)
        for field in ("source_records", "loaded", "duplicates", "rejected"):
            report[field] += int(page_report[field])
        page_latest = latest_last_updated(bundle)
        latest = max(latest, page_latest) if latest and page_latest else latest or page_latest
    if latest:
        with connection.cursor() as cursor:
            cursor.execute(
                """insert into operational.ingestion_checkpoint
                   (pipeline_name, source_system, resource_type, watermark_at, last_successful_run_id)
                   values (%s,%s,%s,%s,null)
                   on conflict (pipeline_name, source_system, resource_type) do update
                   set watermark_at=excluded.watermark_at, updated_at=current_timestamp""",
                (pipeline_name, source_system, resource_type, latest),
            )
        connection.commit()
    report["new_watermark"] = latest
    return report


def execute_sql_file(connection: Any, path: Path) -> None:
    """Execute one controlled project SQL file as a transaction."""
    sql_parts: list[str] = []
    for line in path.read_text().splitlines():
        if line.startswith("\\ir "):
            included = path.parent / line.removeprefix("\\ir ").strip()
            sql_parts.append(included.read_text())
        else:
            sql_parts.append(line)
    with connection.cursor() as cursor:
        cursor.execute("\n".join(sql_parts))
    connection.commit()


def database_quality_report(connection: Any) -> dict[str, int]:
    """Summarize the primary Phase 1 quality and reconciliation controls."""
    checks = {
        "patients": "select count(*) from core.patient",
        "encounters": "select count(*) from core.encounter",
        "observations": "select count(*) from core.observation",
        "organizations": "select count(*) from core.organization",
        "providers": "select count(*) from core.provider",
        "coverages": "select count(*) from core.coverage",
        "conditions": "select count(*) from core.condition_occurrence",
        "procedures": "select count(*) from core.procedure_occurrence",
        "medication_requests": "select count(*) from core.medication_request",
        "orphan_observations": """select count(*) from core.observation o
            left join core.patient p on p.patient_id=o.patient_id where p.patient_id is null""",
        "invalid_encounter_periods": "select count(*) from core.encounter where end_at < start_at",
        "quarantined_fhir_records": "select count(*) from quarantine.fhir_resource",
    }
    result: dict[str, int] = {}
    with connection.cursor() as cursor:
        for name, query in checks.items():
            cursor.execute(query)
            result[name] = int(cursor.fetchone()[0])
    return result


def run_fhir_database_pipeline(connection: Any, payload: dict[str, Any], sql_root: Path, source_system: str = "synthea") -> dict[str, Any]:
    """Load raw FHIR, build the core model, and return auditable quality results."""
    ingestion = load_fhir_payload(connection, payload, source_system)
    execute_sql_file(connection, sql_root / "core" / "021_load_core.sql")
    return {"ingestion": ingestion, "quality": database_quality_report(connection)}


def load_core_and_report(connection: Any, sql_root: Path) -> dict[str, int]:
    """Run only the idempotent staging-to-core transformation and its quality report."""
    execute_sql_file(connection, sql_root / "core" / "021_load_core.sql")
    return database_quality_report(connection)
