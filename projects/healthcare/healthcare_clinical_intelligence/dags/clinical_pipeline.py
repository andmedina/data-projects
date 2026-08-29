"""Runnable Airflow DAG for the synthetic FHIR-to-core workflow."""

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.bash import BashOperator

    with DAG(
        dag_id="clinical_fhir_pipeline",
        start_date=datetime(2025, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["healthcare", "fhir"],
    ) as dag:
        ingest = BashOperator(
            task_id="ingest_validate_and_quarantine_fhir",
            bash_command=(
                "python -m healthcare_clinical_intelligence.cli fhir-postgres "
                "/opt/hci/data/samples/fhir_bundle.json --source-system synthea "
                "--dsn \"$HCI_DATABASE_DSN\""
            ),
        )
        core = BashOperator(
            task_id="transform_and_load_core",
            bash_command=(
                "python -m healthcare_clinical_intelligence.cli core-load "
                "--sql-root /opt/hci/sql --dsn \"$HCI_DATABASE_DSN\""
            ),
        )
        quality = BashOperator(
            task_id="publish_quality_report",
            bash_command="python -m healthcare_clinical_intelligence.cli quality-report --dsn \"$HCI_DATABASE_DSN\"",
        )
        ingest >> core >> quality
except ModuleNotFoundError:
    # Allows source inspection and tests without Airflow installed.
    dag = None
