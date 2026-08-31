from pathlib import Path

from healthcare_clinical_intelligence.quality import QUALITY_CHECK_QUERIES, evaluate_quality_status, gate_status


def test_quality_status_respects_threshold_and_severity() -> None:
    assert evaluate_quality_status(0, 0, "error") == "pass"
    assert evaluate_quality_status(2, 2, "error") == "pass"
    assert evaluate_quality_status(3, 2, "error") == "fail"
    assert evaluate_quality_status(1, 0, "warning") == "warn"


def test_gate_fails_critical_results_and_optional_strict_warnings() -> None:
    passing = [{"status": "pass"}]
    warnings = [{"status": "pass"}, {"status": "warn"}]
    failures = [{"status": "pass"}, {"status": "fail"}]

    assert gate_status(passing) == "passed"
    assert gate_status(warnings) == "passed_with_warnings"
    assert gate_status(warnings, fail_on_warning=True) == "failed"
    assert gate_status(failures) == "failed"
    assert gate_status([]) == "failed"


def test_airflow_dag_enforces_persistent_quality_gate() -> None:
    dag_source = Path("dags/clinical_pipeline.py").read_text()

    assert 'task_id="enforce_quality_gate"' in dag_source
    assert "quality-gate" in dag_source
    assert "--triggered-by airflow" in dag_source


def test_lab_completeness_controls_are_registered() -> None:
    assert "final_laboratory_observations_missing_result" in QUALITY_CHECK_QUERIES
    assert "final_laboratory_observations_missing_effective_at" in QUALITY_CHECK_QUERIES


def test_expanded_claim_controls_are_registered() -> None:
    assert "adjusted_claims_missing_original" in QUALITY_CHECK_QUERIES
    assert "claim_line_adjustment_mismatches" in QUALITY_CHECK_QUERIES
    assert "inconsistent_claim_header_attributes" in QUALITY_CHECK_QUERIES


def test_hl7_lifecycle_controls_are_registered() -> None:
    assert "invalid_hl7_encounter_transitions" in QUALITY_CHECK_QUERIES
    assert "hl7_orders_missing_code" in QUALITY_CHECK_QUERIES
    assert "unmapped_hl7_messages" in QUALITY_CHECK_QUERIES
