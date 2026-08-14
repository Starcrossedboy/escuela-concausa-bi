"""
DAG bienal — orquesta la extracción de fuentes con cadencia real bienal/quinquenal (DS-07 CONEVAL).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, "/opt/airflow/src")  # ajustar según la ruta real de montaje en Docker
from ingesta.extractor_coneval import extraer_coneval

default_args = {
    "owner": "diana.alvarez",
    "retries": 2,
    "retry_delay": timedelta(hours=2),
    "email_on_failure": True,
    "email": ["diana.alvarez96@anahuac.mx"],
}

with DAG(
    dag_id="dag_bienal",
    description="Fuentes con cadencia bienal/quinquenal (DS-07 CONEVAL)",
    default_args=default_args,
    schedule="0 0 1 1 *",  # 1 de enero cada año; el extractor valida si hay publicación nueva
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["bienal", "DS-07", "celula-1"],
) as dag:

    extraer_coneval_task = PythonOperator(
        task_id="extraer_coneval",
        python_callable=extraer_coneval,
    )