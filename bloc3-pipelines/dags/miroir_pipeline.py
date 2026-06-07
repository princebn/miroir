"""Miroir Bloc 3 - DAG d'orchestration du pipeline temps reel."""
import os
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

HOME = os.path.expanduser("~")
ROOT = f"{HOME}/Documents/miroir"
PY = f"{ROOT}/.venv/bin/python"
DBT = f"{ROOT}/.venv/bin/dbt"
PYDIR = f"{ROOT}/bloc3-pipelines/python"
DBTDIR = f"{ROOT}/bloc3-pipelines/dbt/miroir"

with DAG(
    dag_id="miroir_pipeline",
    description="Bloc 3 - ingestion Kafka -> Postgres -> dbt -> qualite",
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    default_args={"retries": 0},
    tags=["miroir", "bloc3"],
) as dag:
    produce = BashOperator(
        task_id="produce",
        bash_command=f"{PY} {PYDIR}/produce_transactions.py --rate 1000 --limit 1000",
    )
    consume = BashOperator(
        task_id="consume",
        bash_command=f"{PY} {PYDIR}/consume_to_postgres.py",
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {DBTDIR} && DBT_PROFILES_DIR={DBTDIR} {DBT} build --exclude tag:reference",
    )
    quality = BashOperator(
        task_id="quality",
        bash_command=f"{PY} {PYDIR}/quality_check.py",
    )
    produce >> consume >> dbt_build >> quality
