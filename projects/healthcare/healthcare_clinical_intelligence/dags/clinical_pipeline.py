"""Airflow integration skeleton; enable with the orchestration Compose profile."""

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.empty import EmptyOperator

    with DAG(
        dag_id="clinical_fhir_pipeline",
        start_date=datetime(2025, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["healthcare", "fhir"],
    ) as dag:
        extract = EmptyOperator(task_id="extract_fhir")
        validate = EmptyOperator(task_id="validate_raw")
        transform = EmptyOperator(task_id="transform_staging")
        load = EmptyOperator(task_id="load_core")
        quality = EmptyOperator(task_id="run_quality_tests")
        reconcile = EmptyOperator(task_id="reconcile_counts")
        extract >> validate >> transform >> load >> quality >> reconcile
except ModuleNotFoundError:
    # Allows source inspection and tests without Airflow installed.
    dag = None
