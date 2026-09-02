from pathlib import Path

from healthcare_clinical_intelligence.performance import BENCHMARK_QUERIES, EXPECTED_INDEXES
from healthcare_clinical_intelligence.postgres import _expanded_sql_file


def test_migration_expands_all_controlled_sql_layers() -> None:
    expanded = _expanded_sql_file(Path("sql/000_init.sql"))

    assert "create table if not exists operational.schema_migration" in expanded
    assert "create or replace view operational.pipeline_run_health" in expanded
    assert "create or replace view omop.person" in expanded
    assert "\\ir " not in expanded


def test_performance_contract_covers_operational_and_clinical_access_paths() -> None:
    assert "ix_pipeline_run_status_started_at" in EXPECTED_INDEXES
    assert "ix_encounter_patient_start_at" in EXPECTED_INDEXES
    assert "ix_observation_patient_effective_at" in EXPECTED_INDEXES
    assert {"monthly_ed_utilization", "monthly_claim_cost", "omop_reconciliation", "imaging_activity"} <= set(
        BENCHMARK_QUERIES
    )


def test_ci_smoke_script_uses_a_disposable_database() -> None:
    source = Path("scripts/run_postgres_smoke.py").read_text()

    assert "create database" in source
    assert "drop database" in source
    assert "--ephemeral" in source
    assert "validate_dashboard_bundle" in source
