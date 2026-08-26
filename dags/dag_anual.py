"""
DAG anual — orquesta la extracción de fuentes con periodicidad anual (DS-01 Formato911, DS-08 CONAPO).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, "/opt/airflow/src")  # ajustar según la ruta real de montaje en Docker
from ingesta.extractor_formato911 import extraer_formato911
from ingesta.extractor_conapo import extraer_conapo

default_args = {
    "owner": "diana.alvarez",
    "retries": 2,
    "retry_delay": timedelta(hours=2),
    "email_on_failure": True,
    "email": ["diana.alvarez96@anahuac.mx"],
}

with DAG(
    dag_id="dag_anual",
    description="Fuentes con periodicidad anual (DS-01 Formato911, DS-08 CONAPO)",
    default_args=default_args,
    schedule="0 0 1 1 *",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["anual", "DS-01", "DS-08", "celula-1"],
) as dag:

    extraer_formato911_task = PythonOperator(
        task_id="extraer_formato911",
        python_callable=extraer_formato911,
    )

    extraer_conapo_task = PythonOperator(
        task_id="extraer_conapo",
        python_callable=extraer_conapo,
    )