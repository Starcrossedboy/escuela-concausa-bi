"""
dags/mlflow_monitor_dag.py
-----------------------------
DAG que ejecuta periódicamente `scripts/mlflow_monitor.py` para vigilar
el experimento de ML en producción. Esta es la opción RECOMENDADA de
las dos descritas en docs/monitoreo_alertas.md (la otra es cron plano).

Por qué un DAG de Airflow y no un cron externo, si ya hay Airflow:
- Reusa el scheduler que ya existe: no se levanta un segundo mecanismo
  de programación (mantiene el requisito de "sin stack nuevo").
- Se obtiene gratis: reintentos automáticos, logs centralizados en la
  UI de Airflow, histórico de ejecuciones, alertas de Airflow mismo si
  el chequeo se rompe (via `on_failure_callback`, reusado de
  `common_alerting/airflow_callbacks.py`), y SLA sobre el propio chequeo
  (via `sla_miss_callback`, para detectar si MLflow está tan lento que
  ni el monitor logra consultarlo a tiempo).

Ubicación sugerida en el repo: `dags/mlflow_monitor_dag.py`

Requisito: que `common_alerting/` y `scripts/` estén en el PYTHONPATH
del Airflow (normalmente alcanza con que cuelguen del mismo repo/DAGs
folder, o se agreguen a `PYTHONPATH` en la imagen de Airflow).
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from common_alerting.airflow_callbacks import on_failure_callback, sla_miss_callback
from scripts.mlflow_monitor import main as ejecutar_monitor_mlflow


def _tarea_verificar_mlflow() -> None:
    """
    Wrapper mínimo alrededor de `mlflow_monitor.main()`.

    Se pasa `argv=[]` a propósito: si no lo hiciéramos, `argparse` (usado
    dentro de `main`) intentaría leer `sys.argv` del propio proceso de
    Airflow (que no tiene nada que ver con este script) y fallaría o
    tomaría argumentos incorrectos. Con `argv=[]` forzamos a que TODA la
    configuración (experimento, métrica, rangos) salga de las variables
    de entorno definidas en el Deployment/Docker Compose de Airflow.
    """
    codigo_salida = ejecutar_monitor_mlflow(argv=[])
    if codigo_salida != 0:
        # Por defecto `main()` siempre retorna 0 (ver nota en
        # mlflow_monitor.py), pero si tu equipo decide cambiar eso,
        # este wrapper ya está preparado para propagar el fallo y que
        # `on_failure_callback` también se dispare.
        raise RuntimeError("mlflow_monitor.py terminó con código de error.")


default_args = {
    "owner": "ml-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    # Si ESTE chequeo falla (por ejemplo, MLflow no responde y el script
    # lanza una excepción no controlada), también se avisa por el mismo
    # webhook. Es una alerta "el monitor no pudo monitorear", distinta
    # de la alerta "el modelo está mal" que manda mlflow_monitor.py.
    "on_failure_callback": on_failure_callback,
}

with DAG(
    dag_id="mlflow_monitor",
    description="Vigila el ultimo run de MLflow y alerta si fallo o si una metrica esta fuera de rango.",
    default_args=default_args,
    # Cada 30 minutos por default; ajustar segun la frecuencia real de
    # entrenamiento/scoring del experimento vigilado.
    schedule_interval="*/30 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    sla_miss_callback=sla_miss_callback,
    tags=["monitoreo", "mlflow", "ml"],
) as dag:

    verificar_mlflow = PythonOperator(
        task_id="verificar_ultimo_run_mlflow",
        python_callable=_tarea_verificar_mlflow,
        # Si esta task tarda mas de 5 minutos (por ejemplo porque MLflow
        # esta lento o caido y las requests hacen timeout), se dispara
        # sla_miss_callback ademas de cualquier reintento normal.
        sla=timedelta(minutes=5),
    )
