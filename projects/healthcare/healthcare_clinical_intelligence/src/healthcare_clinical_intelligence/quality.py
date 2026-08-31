"""Persistent PostgreSQL data-quality checks and pipeline gate behavior."""

from __future__ import annotations

import json
import uuid
from typing import Any


QUALITY_CHECK_QUERIES = {
    "orphan_observations": """
        select count(*) from core.observation o
        left join core.patient p on p.patient_id = o.patient_id
        where p.patient_id is null
    """,
    "invalid_encounter_periods": """
        select count(*) from core.encounter
        where end_at < start_at
    """,
    "completed_ed_encounters_missing_start": """
        select count(*) from core.encounter
        where encounter_class = 'EMER'
          and encounter_status in ('finished', 'completed')
          and start_at is null
    """,
    "active_coverages_missing_period": """
        select count(*) from core.coverage
        where coverage_status = 'active'
          and (coverage_start is null or coverage_end is null)
    """,
    "overlapping_active_coverages": """
        select count(*)
        from core.coverage first_coverage
        join core.coverage second_coverage
          on second_coverage.patient_id = first_coverage.patient_id
         and second_coverage.payer_organization_id is not distinct from first_coverage.payer_organization_id
         and second_coverage.coverage_id > first_coverage.coverage_id
         and second_coverage.coverage_status = 'active'
         and second_coverage.coverage_start <= first_coverage.coverage_end
         and first_coverage.coverage_start <= second_coverage.coverage_end
        where first_coverage.coverage_status = 'active'
          and first_coverage.coverage_start is not null
          and first_coverage.coverage_end is not null
          and second_coverage.coverage_start is not null
          and second_coverage.coverage_end is not null
    """,
    "claim_header_line_mismatches": """
        select count(*) from (
            select c.claim_id
            from core.claim c
            left join core.claim_line cl on cl.claim_id = c.claim_id
            group by c.claim_id, c.billed_amount, c.allowed_amount, c.paid_amount,
                     c.patient_responsibility_amount, c.adjustment_amount
            having count(cl.claim_line_id) = 0
                or c.billed_amount <> sum(cl.billed_amount)
                or c.allowed_amount <> sum(cl.allowed_amount)
                or c.paid_amount <> sum(cl.paid_amount)
                or c.patient_responsibility_amount <> sum(cl.patient_responsibility_amount)
                or c.adjustment_amount <> sum(cl.adjustment_amount)
        ) mismatches
    """,
    "orphan_claim_lines": """
        select count(*) from core.claim_line cl
        left join core.claim c on c.claim_id = cl.claim_id
        where c.claim_id is null
    """,
    "adjusted_claims_missing_original": """
        select count(*) from core.claim adjusted
        left join core.claim original on original.claim_id = adjusted.original_claim_id
        where adjusted.claim_frequency_code in ('7', '8')
          and original.claim_id is null
    """,
    "claim_line_adjustment_mismatches": """
        select count(*) from (
            select cl.claim_line_id
            from core.claim_line cl
            left join core.claim_line_adjustment adjustment
              on adjustment.claim_line_id = cl.claim_line_id
            group by cl.claim_line_id, cl.adjustment_amount
            having cl.adjustment_amount <> coalesce(sum(adjustment.adjustment_amount), 0)
        ) mismatches
    """,
    "inconsistent_claim_header_attributes": """
        select count(*) from (
            select claim_id
            from staging.stg_claim_line
            group by claim_id
            having count(distinct patient_id) > 1
                or count(distinct coalesce(payer_id, '')) > 1
                or count(distinct coalesce(billing_provider_id, '')) > 1
                or count(distinct claim_frequency_code) > 1
                or count(distinct coalesce(original_claim_id, '')) > 1
                or count(distinct coalesce(diagnosis_codes, '')) > 1
        ) inconsistent_claims
    """,
    "invalid_hl7_encounter_transitions": """
        select count(*) from (
            select event_code,
                   lag(event_code) over (
                       partition by encounter_id
                       order by event_at, hl7_encounter_event_id
                   ) as previous_event_code
            from core.hl7_encounter_event
        ) timeline
        where (event_code = 'A01' and previous_event_code is not null)
           or (event_code in ('A02', 'A03', 'A08')
               and coalesce(previous_event_code, '') not in ('A01', 'A02', 'A08'))
           or previous_event_code = 'A03'
    """,
    "hl7_orders_missing_code": """
        select count(*) from core.hl7_order_event
        where nullif(btrim(code), '') is null
    """,
    "unmapped_hl7_messages": """
        select count(*) from raw.hl7_message message
        where (message.message_type like 'ADT^%'
               and not exists (
                   select 1 from core.hl7_encounter_event event
                   where event.message_control_id = message.message_control_id
               ))
           or (message.message_type = 'ORM^O01'
               and not exists (
                   select 1 from core.hl7_order_event order_event
                   where order_event.message_control_id = message.message_control_id
               ))
           or (message.message_type = 'ORU^R01'
               and not exists (
                   select 1 from core.hl7_observation observation
                   where observation.message_control_id = message.message_control_id
               ))
    """,
    "final_laboratory_observations_missing_result": """
        select count(*) from core.observation
        where category_code = 'laboratory'
          and observation_status in ('final', 'amended', 'corrected')
          and data_absent_reason_code is null
          and case value_type
              when 'Quantity' then value_numeric is null
              when 'Integer' then value_numeric is null
              when 'String' then nullif(btrim(value_text), '') is null
              when 'Boolean' then value_boolean is null
              when 'CodeableConcept' then value_code is null and nullif(btrim(value_code_display), '') is null
              else true
          end
    """,
    "final_laboratory_observations_missing_effective_at": """
        select count(*) from core.observation
        where category_code = 'laboratory'
          and observation_status in ('final', 'amended', 'corrected')
          and effective_at is null
    """,
    "quarantined_fhir_records": "select count(*) from quarantine.fhir_resource",
    "quarantined_claim_lines": "select count(*) from quarantine.claim_line",
    "quarantined_hl7_messages": "select count(*) from quarantine.hl7_message",
}


def evaluate_quality_status(observed_value: int, failure_threshold: int, severity: str) -> str:
    """Classify one observed value against its configured tolerance."""
    if observed_value <= failure_threshold:
        return "pass"
    return "warn" if severity == "warning" else "fail"


def gate_status(results: list[dict[str, Any]], fail_on_warning: bool = False) -> str:
    """Return the run outcome that controls the CLI process exit code."""
    if not results:
        return "failed"
    if any(result["status"] in {"fail", "error"} for result in results):
        return "failed"
    if any(result["status"] == "warn" for result in results):
        return "failed" if fail_on_warning else "passed_with_warnings"
    return "passed"


def run_quality_gate(
    connection: Any,
    triggered_by: str = "cli",
    pipeline_run_id: str | None = None,
    fail_on_warning: bool = False,
) -> dict[str, Any]:
    """Evaluate enabled controls, persist evidence, and return the gate outcome."""
    quality_run_id = str(uuid.uuid4())
    results: list[dict[str, Any]] = []
    with connection.cursor() as cursor:
        cursor.execute(
            """insert into operational.quality_run
               (quality_run_id, pipeline_run_id, triggered_by, status, fail_on_warning)
               values (%s,%s,%s,'running',%s)""",
            (quality_run_id, pipeline_run_id, triggered_by, fail_on_warning),
        )
        cursor.execute(
            """select check_name, description, quality_dimension, severity, failure_threshold
               from operational.quality_check_definition
               where enabled
               order by check_name"""
        )
        definitions = cursor.fetchall()

        for check_name, description, dimension, severity, threshold in definitions:
            query = QUALITY_CHECK_QUERIES.get(check_name)
            observed_value: int | None = None
            details: dict[str, Any] = {"description": description}
            if query is None:
                status = "error"
                details["error"] = "No executable query is registered for this enabled check"
            else:
                cursor.execute("savepoint quality_check_execution")
                try:
                    cursor.execute(query)
                    observed_value = int(cursor.fetchone()[0])
                    status = evaluate_quality_status(observed_value, int(threshold), severity)
                except Exception as exc:
                    cursor.execute("rollback to savepoint quality_check_execution")
                    status = "error"
                    details["error"] = str(exc)
                finally:
                    cursor.execute("release savepoint quality_check_execution")

            cursor.execute(
                """insert into operational.quality_result
                   (quality_run_id, check_name, quality_dimension, severity,
                    observed_value, failure_threshold, status, details)
                   values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                (quality_run_id, check_name, dimension, severity, observed_value, threshold, status, json.dumps(details)),
            )
            results.append(
                {
                    "check_name": check_name,
                    "dimension": dimension,
                    "severity": severity,
                    "observed_value": observed_value,
                    "failure_threshold": int(threshold),
                    "status": status,
                }
            )

        overall_status = gate_status(results, fail_on_warning)
        cursor.execute(
            """update operational.quality_run
               set status=%s, completed_at=current_timestamp
               where quality_run_id=%s""",
            (overall_status, quality_run_id),
        )
    connection.commit()
    warning_count = sum(result["status"] == "warn" for result in results)
    failure_count = sum(result["status"] in {"fail", "error"} for result in results) + int(not results)
    return {
        "quality_run_id": quality_run_id,
        "pipeline_run_id": pipeline_run_id,
        "triggered_by": triggered_by,
        "fail_on_warning": fail_on_warning,
        "status": overall_status,
        "checks": len(results),
        "passed": sum(result["status"] == "pass" for result in results),
        "warnings": warning_count,
        "failures": failure_count,
        "blocking_results": failure_count + (warning_count if fail_on_warning else 0),
        "results": results,
    }
