"""
DAG diario — orquesta la extracción de fuentes con periodicidad diaria (DS-06 CONAGUA SINA).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, "/opt/airflow/src")  # ajustar según la ruta real de montaje en Docker
from ingesta.extractor_conagua import extraer_conagua

default_args = {
    "owner": "diana.alvarez",
    "retries": 2,
    "retry_delay": timedelta(minutes=15),
    "email_on_failure": True,
    "email": ["diana.alvarez96@anahuac.mx"],
}

with DAG(
    dag_id="dag_diario",
    description="Fuentes con periodicidad diaria (DS-06 CONAGUA SINA)",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["diario", "DS-06", "celula-1"],
) as dag:

    extraer_conagua_task = PythonOperator(
        task_id="extraer_conagua",
        python_callable=extraer_conagua,
    )