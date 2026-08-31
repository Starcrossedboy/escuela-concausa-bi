"""
tests/common_alerting/test_webhook.py
----------------------------------------
Tests unitarios para common_alerting/webhook.py.

Enfoque: NO se hace ningún request real a Slack/Discord. Se usa
`monkeypatch` (fixture nativa de pytest) para:
  - controlar las variables de entorno que lee el módulo, y
  - reemplazar `requests.post` por una función falsa que devuelve lo
    que nosotros decidamos, sin tocar la red.

Esto hace que los tests sean rápidos, deterministas y corran igual en
cualquier máquina (CI, laptop, etc.) sin necesitar credenciales ni
conectividad real a un webhook.
"""

import json

import pytest

from common_alerting import webhook


class RespuestaFalsa:
    """Simula el objeto que retorna requests.post(...)."""

    def __init__(self, status_code: int = 200):
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise webhook.requests.HTTPError(f"HTTP {self.status_code}")


def test_no_envia_nada_si_falta_url(monkeypatch, caplog):
    """
    Si ALERT_WEBHOOK_URL no está definida, enviar_alerta() no debe
    intentar hacer ningún request, y debe loguear un warning.
    """
    monkeypatch.delenv(webhook.ALERT_WEBHOOK_URL_ENV, raising=False)

    llamadas = []
    monkeypatch.setattr(
        webhook.requests, "post", lambda *a, **k: llamadas.append((a, k))
    )

    with caplog.at_level("WARNING"):
        webhook.enviar_alerta("Título", "Texto")

    assert llamadas == []
    assert "no está definida" in caplog.text


def test_envia_payload_formato_slack_por_default(monkeypatch):
    """
    Sin ALERT_WEBHOOK_TYPE definida, el default debe ser "slack", y el
    payload debe tener la forma {"text": "*titulo*\\ntexto"}.
    """
    monkeypatch.setenv(webhook.ALERT_WEBHOOK_URL_ENV, "https://ejemplo.test/webhook")
    monkeypatch.delenv(webhook.ALERT_WEBHOOK_TYPE_ENV, raising=False)

    llamadas = []

    def _post_falso(url, data=None, headers=None, timeout=None):
        llamadas.append({"url": url, "data": data, "headers": headers, "timeout": timeout})
        return RespuestaFalsa(status_code=200)

    monkeypatch.setattr(webhook.requests, "post", _post_falso)

    webhook.enviar_alerta("Alerta de prueba", "Detalle de la alerta")

    assert len(llamadas) == 1
    llamada = llamadas[0]
    assert llamada["url"] == "https://ejemplo.test/webhook"

    payload = json.loads(llamada["data"])
    assert payload == {"text": "*Alerta de prueba*\nDetalle de la alerta"}
    assert llamada["timeout"] == webhook.REQUEST_TIMEOUT_SECONDS


def test_envia_payload_formato_discord(monkeypatch):
    """
    Con ALERT_WEBHOOK_TYPE=discord, el payload debe usar la estructura
    de "embeds" en vez de "text".
    """
    monkeypatch.setenv(webhook.ALERT_WEBHOOK_URL_ENV, "https://ejemplo.test/webhook")
    monkeypatch.setenv(webhook.ALERT_WEBHOOK_TYPE_ENV, "discord")

    llamadas = []

    def _post_falso(url, data=None, headers=None, timeout=None):
        llamadas.append(data)
        return RespuestaFalsa(status_code=200)

    monkeypatch.setattr(webhook.requests, "post", _post_falso)

    webhook.enviar_alerta("Título Discord", "Texto Discord")

    payload = json.loads(llamadas[0])
    assert "embeds" in payload
    assert payload["embeds"][0]["title"] == "Título Discord"
    assert payload["embeds"][0]["description"] == "Texto Discord"
    assert payload["embeds"][0]["color"] == 15158332


def test_no_propaga_excepcion_si_webhook_falla(monkeypatch, caplog):
    """
    Requisito de diseño explícito en el docstring de enviar_alerta():
    un fallo al notificar (por ejemplo un 500 del webhook) NUNCA debe
    propagar una excepción hacia quien llamó a enviar_alerta().
    """
    monkeypatch.setenv(webhook.ALERT_WEBHOOK_URL_ENV, "https://ejemplo.test/webhook")

    def _post_que_falla(*a, **k):
        return RespuestaFalsa(status_code=500)

    monkeypatch.setattr(webhook.requests, "post", _post_que_falla)

    with caplog.at_level("ERROR"):
        webhook.enviar_alerta("Título", "Texto")  # no debe lanzar

    assert "No se pudo enviar la alerta" in caplog.text


def test_no_propaga_excepcion_si_hay_error_de_red(monkeypatch, caplog):
    """
    Mismo requisito que el test anterior, pero simulando un error de
    conexión (ej. DNS caído, timeout) en vez de un status code 4xx/5xx.
    """
    monkeypatch.setenv(webhook.ALERT_WEBHOOK_URL_ENV, "https://ejemplo.test/webhook")

    def _post_que_lanza_error_de_red(*a, **k):
        raise webhook.requests.ConnectionError("no se pudo conectar")

    monkeypatch.setattr(webhook.requests, "post", _post_que_lanza_error_de_red)

    with caplog.at_level("ERROR"):
        webhook.enviar_alerta("Título", "Texto")  # no debe lanzar

    assert "No se pudo enviar la alerta" in caplog.text
