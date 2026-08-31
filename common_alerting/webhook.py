"""
common_alerting/webhook.py
---------------------------
Módulo compartido de bajo nivel: SOLO sabe mandar un mensaje a un webhook
de Slack o Discord. No sabe nada de Airflow ni de MLflow a propósito.

Por qué existe este módulo separado (decisión de diseño):
- Tanto los callbacks de Airflow (`airflow_callbacks.py`) como el script
  de monitoreo de MLflow (`mlflow_monitor.py`) necesitan "avisar por
  Slack/Discord". Si escribimos esa lógica dos veces, el día que cambie
  el formato del webhook o la URL, hay que acordarse de tocar los dos
  lugares. Centralizarlo en un módulo importable elimina ese riesgo.
- Mantenerlo "tonto" (sin lógica de negocio) lo hace fácil de testear:
  se puede probar con un webhook falso (por ejemplo con `responses` o
  `requests_mock`) sin tener que simular un DAG de Airflow ni un
  experimento de MLflow.

Ubicación sugerida en el repo: `common_alerting/webhook.py`
(junto a `common_alerting/airflow_callbacks.py`).
"""

import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Nombre de la variable de entorno que contiene la URL del webhook.
# NUNCA se hardcodea la URL en el código: siempre se lee de acá.
# En Airflow, esta env var se define en el docker-compose / values.yaml
# de k8s / Airflow Variables (via `{{ var.value.ALERT_WEBHOOK_URL }}`
# si prefieren usar el backend de Variables en vez de env vars puras).
ALERT_WEBHOOK_URL_ENV = "ALERT_WEBHOOK_URL"

# "slack" o "discord". Cada plataforma espera un JSON distinto en el
# body del POST, así que necesitamos saber a cuál le estamos hablando.
ALERT_WEBHOOK_TYPE_ENV = "ALERT_WEBHOOK_TYPE"

# Timeout corto a propósito: si Slack/Discord está lento o caído, no
# queremos que un worker de Airflow (o un cron) se quede colgado
# esperando la respuesta del webhook.
REQUEST_TIMEOUT_SECONDS = 5


def _obtener_configuracion_webhook() -> tuple[str | None, str]:
    """
    Lee la URL y el tipo de webhook desde variables de entorno.

    Retorna (url, tipo). Si `url` es None, quien llame debe decidir no
    enviar nada. Esto es a propósito "fail-safe": preferimos que falte
    una alerta a que un webhook mal configurado tumbe un DAG completo.
    """
    url = os.environ.get(ALERT_WEBHOOK_URL_ENV)
    tipo = os.environ.get(ALERT_WEBHOOK_TYPE_ENV, "slack").lower()
    return url, tipo


def _construir_payload(tipo: str, titulo: str, texto: str) -> dict[str, Any]:
    """
    Arma el cuerpo JSON según la plataforma destino.

    Slack (Incoming Webhooks) espera un campo "text".
    Discord espera "content" o, para algo más prolijo, una lista de
    "embeds". Usamos un embed simple en rojo para que la alerta
    resalte visualmente en el canal.
    """
    if tipo == "discord":
        return {
            "embeds": [
                {
                    "title": titulo,
                    "description": texto,
                    "color": 15158332,  # rojo (0xE74C3C) para alertas
                }
            ]
        }

    # Default: formato Slack.
    return {"text": f"*{titulo}*\n{texto}"}


def enviar_alerta(titulo: str, texto: str) -> None:
    """
    Envía una alerta al webhook configurado por variables de entorno.

    Decisión clave: esta función NUNCA propaga excepciones hacia arriba.
    Si el POST al webhook falla (red caída, webhook mal configurado,
    Slack devolviendo 500), lo único que pasa es que queda un log de
    error. Un fallo al notificar NO debe convertirse en un segundo
    incidente (por ejemplo, tapar el error real de Airflow/MLflow con
    un traceback de `requests` sin relación con el problema original).
    """
    url, tipo = _obtener_configuracion_webhook()

    if not url:
        logger.warning(
            "No se envió la alerta '%s': la variable de entorno %s no está definida.",
            titulo,
            ALERT_WEBHOOK_URL_ENV,
        )
        return

    payload = _construir_payload(tipo, titulo, texto)

    try:
        respuesta = requests.post(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        respuesta.raise_for_status()
        logger.info("Alerta enviada correctamente: %s", titulo)
    except requests.RequestException as error:
        # Se loguea pero no se relanza: ver docstring de la función.
        logger.error("No se pudo enviar la alerta al webhook (%s): %s", tipo, error)
