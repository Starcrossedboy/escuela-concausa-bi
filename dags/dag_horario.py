"""
DAG horario — orquesta la extracción de fuentes con periodicidad horaria (DS-05 SINAICA).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, "/opt/airflow/src")  # ajustar según la ruta real de montaje en Docker
from ingesta.extractor_sinaica import extraer_sinaica

default_args = {
    "owner": "diana.alvarez",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["diana.alvarez96@anahuac.mx"],
}

with DAG(
    dag_id="dag_horario",
    description="Fuentes con periodicidad horaria (DS-05 SINAICA)",
    default_args=default_args,
    schedule="@hourly",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["horario", "DS-05", "celula-1"],
) as dag:

    extraer_sinaica_task = PythonOperator(
        task_id="extraer_sinaica",
        python_callable=extraer_sinaica,
    )