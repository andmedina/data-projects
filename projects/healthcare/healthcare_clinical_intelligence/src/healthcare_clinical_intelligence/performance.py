"""Small PostgreSQL performance guardrails for repeatable development validation."""

from __future__ import annotations

from typing import Any

EXPECTED_INDEXES = {
    "ix_pipeline_run_status_started_at",
    "ix_pipeline_run_name_started_at",
    "ix_raw_fhir_resource_type_id",
    "ix_raw_fhir_resource_run_id",
    "ix_raw_claim_line_run_id",
    "ix_raw_hl7_message_run_id",
    "ix_encounter_patient_start_at",
    "ix_observation_patient_effective_at",
    "ix_condition_patient_recorded_at",
    "ix_procedure_patient_performed_at",
    "ix_medication_patient_authored_at",
    "ix_coverage_member_period",
}

BENCHMARK_QUERIES = {
    "executive_core_counts": """
        select (select count(*) from core.patient),
               (select count(*) from core.encounter),
               (select count(*) from core.observation)
    """,
    "monthly_ed_utilization": "select * from mart.ed_utilization_monthly order by reporting_month",
    "monthly_claim_cost": "select * from mart.claim_cost_monthly order by reporting_month",
    "omop_reconciliation": "select * from omop.domain_row_count order by domain_name",
    "imaging_activity": "select * from mart.imaging_activity_monthly order by reporting_month",
}


def database_performance_report(connection: Any, maximum_query_ms: float = 5000.0) -> dict[str, Any]:
    """Check required indexes and capture real execution times for representative marts."""
    with connection.cursor() as cursor:
        cursor.execute(
            """select indexname
               from pg_indexes
               where schemaname in ('operational', 'raw', 'core')"""
        )
        present_indexes = {str(row[0]) for row in cursor.fetchall()}
        benchmarks = []
        for name, query in BENCHMARK_QUERIES.items():
            cursor.execute(f"explain (analyze, buffers, format json) {query}")
            plan_document = cursor.fetchone()[0]
            plan = plan_document[0] if isinstance(plan_document, list) else plan_document
            execution_ms = float(plan["Execution Time"])
            planning_ms = float(plan["Planning Time"])
            benchmarks.append(
                {
                    "name": name,
                    "planning_ms": planning_ms,
                    "execution_ms": execution_ms,
                    "within_threshold": execution_ms <= maximum_query_ms,
                }
            )
    missing_indexes = sorted(EXPECTED_INDEXES - present_indexes)
    slow_queries = [item["name"] for item in benchmarks if not item["within_threshold"]]
    return {
        "status": "passed" if not missing_indexes and not slow_queries else "failed",
        "maximum_query_ms": maximum_query_ms,
        "expected_indexes": len(EXPECTED_INDEXES),
        "missing_indexes": missing_indexes,
        "slow_queries": slow_queries,
        "benchmarks": benchmarks,
    }
