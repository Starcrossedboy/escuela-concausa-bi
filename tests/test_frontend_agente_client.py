"""Pruebas del cliente HTTP del widget de chat (US-305)."""

from __future__ import annotations

import httpx
import pytest

from src.frontend.agente_client import consultar_agente


class RespuestaHTTPFake:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


def test_consulta_el_endpoint_con_el_contrato_canonico() -> None:
    def post(url: str, **kwargs) -> RespuestaHTTPFake:
        assert url == "http://api:8000/api/v1/agente/consulta"
        assert kwargs["json"] == {"pregunta": "Cuantas escuelas hay?"}
        assert kwargs["headers"] is None
        assert kwargs["timeout"] == 15.0
        return RespuestaHTTPFake(
            {
                "respuesta": "Hay cuatro escuelas.",
                "sql_generado": "SELECT count(*) FROM gold.dim_escuela",
                "fuera_de_alcance": False,
            }
        )

    respuesta = consultar_agente(
        "http://api:8000/",
        " Cuantas escuelas hay? ",
        post=post,
    )

    assert respuesta.respuesta == "Hay cuatro escuelas."
    assert respuesta.sql_generado == "SELECT count(*) FROM gold.dim_escuela"
    assert not respuesta.fuera_de_alcance


def test_propaga_access_token_como_bearer() -> None:
    def post(url: str, **kwargs) -> RespuestaHTTPFake:
        assert kwargs["headers"] == {"Authorization": "Bearer jwt-prueba"}
        return RespuestaHTTPFake(
            {
                "respuesta": "Respuesta autenticada.",
                "sql_generado": None,
                "fuera_de_alcance": False,
            }
        )

    respuesta = consultar_agente(
        "http://api:8000",
        "Pregunta autenticada",
        post=post,
        access_token="jwt-prueba",
    )

    assert respuesta.respuesta == "Respuesta autenticada."


@pytest.mark.parametrize("pregunta", ["x", "x" * 501])
def test_rechaza_preguntas_fuera_del_tamano_del_contrato(pregunta: str) -> None:
    with pytest.raises(ValueError, match="entre 3 y 500"):
        consultar_agente("http://api:8000", pregunta)


@pytest.mark.parametrize(
    "payload",
    [
        {"respuesta": "Incompleta"},
        {"respuesta": None, "sql_generado": None, "fuera_de_alcance": False},
        {"respuesta": "Texto", "sql_generado": 42, "fuera_de_alcance": False},
        {"respuesta": "Texto", "sql_generado": None, "fuera_de_alcance": "false"},
    ],
)
def test_rechaza_una_respuesta_con_contrato_invalido(payload: dict) -> None:
    def post(*args, **kwargs) -> RespuestaHTTPFake:
        return RespuestaHTTPFake(payload)

    with pytest.raises(ValueError, match="respuesta de agente inválida"):
        consultar_agente("http://api:8000", "Pregunta valida", post=post)


def test_convierte_un_error_http_en_error_de_conexion() -> None:
    def post(*args, **kwargs) -> RespuestaHTTPFake:
        request = httpx.Request("POST", "http://api:8000/api/v1/agente/consulta")
        raise httpx.ConnectError("sin conexión", request=request)

    with pytest.raises(ConnectionError, match="API del agente no está disponible"):
        consultar_agente("http://api:8000", "Pregunta valida", post=post)