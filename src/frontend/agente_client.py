"""Cliente HTTP del agente FARO para el widget de US-305."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class RespuestaAgente:
    """Respuesta estable del contrato `AgenteRespuestaOut`."""

    respuesta: str
    sql_generado: str | None
    fuera_de_alcance: bool


def consultar_agente(
    api_base_url: str,
    pregunta: str,
    post: Callable[..., Any] = httpx.post,
) -> RespuestaAgente:
    """Consulta `/api/v1/agente/consulta` y valida su respuesta mínima."""
    texto = pregunta.strip()
    if not 3 <= len(texto) <= 500:
        raise ValueError("La pregunta debe tener entre 3 y 500 caracteres.")

    try:
        response = post(
            f"{api_base_url.rstrip('/')}/api/v1/agente/consulta",
            json={"pregunta": texto},
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise ConnectionError("La API del agente no está disponible.") from exc

    try:
        respuesta = payload["respuesta"]
        sql_generado = payload.get("sql_generado")
        fuera_de_alcance = payload["fuera_de_alcance"]
        if not isinstance(respuesta, str):
            raise TypeError
        if sql_generado is not None and not isinstance(sql_generado, str):
            raise TypeError
        if not isinstance(fuera_de_alcance, bool):
            raise TypeError
        return RespuestaAgente(
            respuesta=respuesta,
            sql_generado=sql_generado,
            fuera_de_alcance=fuera_de_alcance,
        )
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError("La API devolvió una respuesta de agente inválida.") from exc