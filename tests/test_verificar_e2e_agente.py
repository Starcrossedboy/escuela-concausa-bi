"""Pruebas offline de la sonda autenticada de E2E del agente."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from src.agente.verificar_e2e import ErrorVerificacion, verificar_e2e


class _RespuestaHTTP:
    """Respuesta HTTP mínima y determinista para la sonda."""

    status = 200

    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self) -> _RespuestaHTTP:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


class VerificarE2EAgenteTests(unittest.TestCase):
    def test_requiere_url_y_token(self) -> None:
        with self.assertRaisesRegex(ErrorVerificacion, "son obligatorios"):
            verificar_e2e("", "")

    def test_valida_lectura_y_rechazo_de_escritura(self) -> None:
        respuestas = iter(
            [
                _RespuestaHTTP(
                    {
                        "respuesta": "Hay una escuela en riesgo.",
                        "sql_generado": "SELECT cct FROM gold.features_escuela LIMIT 1000;",
                        "fuera_de_alcance": False,
                    }
                ),
                _RespuestaHTTP(
                    {
                        "respuesta": "FARO solo responde consultas de lectura.",
                        "sql_generado": None,
                        "fuera_de_alcance": True,
                    }
                ),
            ]
        )

        with patch("src.agente.verificar_e2e.urlopen", side_effect=respuestas) as urlopen_mock:
            verificar_e2e("https://api.example", "token-efimero")

        self.assertEqual(urlopen_mock.call_count, 2)
        request = urlopen_mock.call_args_list[0].args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer token-efimero")

    def test_rechaza_despliegue_sin_sql_generado(self) -> None:
        respuestas = iter(
            [
                _RespuestaHTTP(
                    {
                        "respuesta": "El agente no está disponible en este entorno todavía.",
                        "sql_generado": None,
                        "fuera_de_alcance": False,
                    }
                )
            ]
        )

        with patch("src.agente.verificar_e2e.urlopen", side_effect=respuestas):
            with self.assertRaisesRegex(ErrorVerificacion, "no están listos"):
                verificar_e2e("https://api.example", "token-efimero")