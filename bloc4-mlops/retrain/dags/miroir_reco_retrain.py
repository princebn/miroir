# Miroir Bloc 4 - DAG de reentrainement hebdo du re-ranker (garde-fous qualite + perf).
import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

HOME = os.path.expanduser("~")
ROOT = HOME + "/Documents/miroir"
PY = ROOT + "/.venv/bin/python"
B4 = ROOT + "/bloc4-mlops"

with DAG(
    dag_id="miroir_reco_retrain",
    description="Bloc 4 - reentrainement hebdo du re-ranker (qualite + promote/rollback)",
    start_date=datetime(2026, 1, 1),
    schedule="@weekly",
    catchup=False,
    default_args={"retries": 0},
    tags=["miroir", "bloc4", "mlops"],
) as dag:
    regenerate = BashOperator(
        task_id="regenerate",
        bash_command=f"cd {B4} && {PY} -m src.synth.generate_interactions && {PY} -m src.reranker.prepare",
    )
    quality_gate = BashOperator(
        task_id="quality_gate",
        bash_command=f"cd {B4} && {PY} retrain/quality_check.py",
    )
    train = BashOperator(
        task_id="train",
        bash_command=f"cd {B4} && {PY} -m src.reranker.train",
    )
    evaluate_promote = BashOperator(
        task_id="evaluate_promote",
        bash_command=f"cd {B4} && {PY} retrain/evaluate_and_promote.py",
    )
    regenerate >> quality_gate >> train >> evaluate_promote
