"""
DAG censal estático — orquesta la extracción de la fuente censal única, sin periodicidad (DS-03 CEMABE).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

import sys
sys.path.insert(0, "/opt/airflow/src")  # ajustar según la ruta real de montaje en Docker
from ingesta.extractor_cemabe import extraer_cemabe

default_args = {
    "owner": "diana.alvarez",
    "retries": 2,
    "retry_delay": timedelta(hours=2),
    "email_on_failure": True,
    "email": ["diana.alvarez96@anahuac.mx"],
}

with DAG(
    dag_id="dag_censal_estatico",
    description="Fuente censal única sin periodicidad (DS-03 CEMABE, snapshot 2013)",
    default_args=default_args,
    schedule=None,  # censo único, sin cadencia real — disparo manual on-demand
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["censal", "estatico", "DS-03", "celula-1"],
) as dag:

    extraer_cemabe_task = PythonOperator(
        task_id="extraer_cemabe",
        python_callable=extraer_cemabe,
    )