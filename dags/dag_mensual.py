"""
DAG mensual — orquesta la extracción de fuentes con periodicidad mensual (DS-04 SESNSP).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, "/opt/airflow/src")  # ajustar según la ruta real de montaje en Docker
from ingesta.extractor_sesnsp import extraer_sesnsp

default_args = {
    "owner": "diana.alvarez",
    "retries": 2,
    "retry_delay": timedelta(minutes=30),
    "email_on_failure": True,
    "email": ["diana.alvarez96@anahuac.mx"],
}

with DAG(
    dag_id="dag_mensual",
    description="Fuentes con periodicidad mensual (DS-04 SESNSP)",
    default_args=default_args,
    schedule="@monthly",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["mensual", "DS-04", "celula-1"],
) as dag:

    extraer_sesnsp_task = PythonOperator(
        task_id="extraer_sesnsp",
        python_callable=extraer_sesnsp,
    )