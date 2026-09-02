"""
common_alerting/airflow_callbacks.py
--------------------------------------
Callbacks reutilizables de Airflow: `on_failure_callback` y
`sla_miss_callback`. Cualquier DAG del repo los importa en vez de
reescribir la lógica de notificación cada vez.

Por qué NO se agrega Prometheus/Grafana/Alertmanager:
- Airflow ya expone estos dos "ganchos" (callbacks) de forma nativa,
  ejecutados por el propio scheduler/worker cuando corresponde. No hace
  falta instrumentar métricas, exponer un endpoint /metrics, ni correr
  un exporter adicional solo para saber "esta task falló" o "este DAG
  incumplió su SLA". Es monitoreo "gratis" que ya viene con Airflow.
- Toda la complejidad de "a quién y cómo avisar" queda en un solo
  módulo (`webhook.py`), así que agregar este monitoreo a un DAG nuevo
  es tan simple como importar dos funciones.

Ubicación sugerida en el repo: `common_alerting/airflow_callbacks.py`

Uso en un DAG:

    from common_alerting.airflow_callbacks import on_failure_callback, sla_miss_callback

    default_args = {
        "on_failure_callback": on_failure_callback,  # a nivel task o DAG
    }

    with DAG(
        ...,
        default_args=default_args,
        sla_miss_callback=sla_miss_callback,  # esto va SIEMPRE a nivel DAG
    ) as dag:
        ...
"""

import logging
from typing import Any

from common_alerting.webhook import enviar_alerta

logger = logging.getLogger(__name__)


def on_failure_callback(context: dict[str, Any]) -> None:
    """
    Se dispara cuando una task (o el DAG, si se define a ese nivel)
    termina en estado failed. Airflow inyecta automáticamente el
    diccionario `context` con la información de la ejecución; no hace
    falta armarlo a mano.

    Se usan `.get()` y `getattr(..., default)` en todos lados a propósito:
    el `context` puede variar levemente según la versión de Airflow o el
    tipo de falla, y no queremos que el CALLBACK DE ALERTA sea la razón
    por la que algo se rompe con un KeyError/AttributeError.
    """
    ti = context.get("task_instance")
    dag_run = context.get("dag_run")
    exception = context.get("exception")

    dag_id = getattr(ti, "dag_id", "desconocido")
    task_id = getattr(ti, "task_id", "desconocido")
    fecha_ejecucion = context.get("execution_date") or getattr(
        dag_run, "execution_date", "N/A"
    )
    log_url = getattr(ti, "log_url", "N/A")
    intento = getattr(ti, "try_number", "N/A")

    titulo = f"🔴 Fallo en Airflow: {dag_id}.{task_id}"
    texto = (
        f"*DAG:* {dag_id}\n"
        f"*Task:* {task_id}\n"
        f"*Intento:* {intento}\n"
        f"*Fecha de ejecución:* {fecha_ejecucion}\n"
        f"*Error:* {exception}\n"
        f"*Logs:* {log_url}"
    )

    enviar_alerta(titulo, texto)


def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis) -> None:
    """
    Se dispara cuando Airflow detecta que una o más tasks incumplieron
    su SLA declarado (`sla=timedelta(...)` en la task).

    La firma de esta función (los 5 parámetros posicionales) NO es
    arbitraria: es exactamente la que Airflow espera para
    `sla_miss_callback`. Si se cambia el orden o los nombres, Airflow
    fallará al invocarlo (o lo hará con los argumentos desalineados).

    Nota importante para quien configure DAGs nuevos: si ninguna task
    define `sla=...`, este callback nunca se va a disparar, aunque esté
    correctamente conectado al DAG.
    """
    dag_id = getattr(dag, "dag_id", "desconocido")

    titulo = f"🟠 SLA incumplido en Airflow: {dag_id}"
    texto = (
        f"*DAG:* {dag_id}\n"
        f"*Tasks con SLA incumplido:* {task_list}\n"
        f"*Tasks bloqueantes:* {blocking_task_list}\n"
        f"*Detalle de SLAs:* {slas}"
    )

    enviar_alerta(titulo, texto)
