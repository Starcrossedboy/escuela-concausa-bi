"""Orquestación segura e inyectable del agente FARO (US-304a)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.agente.guardrails import pregunta_en_alcance, preparar_sql_seguro
from src.agente.prompt import construir_prompt_sistema

RecuperarContexto = Callable[[str], str]
GenerarSQL = Callable[[str, str], str]
EjecutarSQL = Callable[[str], Sequence[Mapping[str, Any]]]
RedactarRespuesta = Callable[[str, Sequence[Mapping[str, Any]]], str]


@dataclass(frozen=True)
class ResultadoConsulta:
    """Resultado interno alineado con el contrato público del agente."""

    respuesta: str
    sql_generado: str | None
    fuera_de_alcance: bool


def procesar_consulta(
    pregunta: str,
    recuperar_contexto: RecuperarContexto,
    generar_sql: GenerarSQL,
    ejecutar_sql: EjecutarSQL,
    redactar_respuesta: RedactarRespuesta,
) -> ResultadoConsulta:
    """Procesa una pregunta sin acoplarse a RAG, LLM, base de datos ni API."""
    alcance = pregunta_en_alcance(pregunta)
    if not alcance.permitido:
        return ResultadoConsulta(
            respuesta=alcance.razon or "Pregunta fuera del alcance de FARO.",
            sql_generado=None,
            fuera_de_alcance=True,
        )

    contexto = recuperar_contexto(pregunta)
    prompt = construir_prompt_sistema(contexto)
    try:
        sql_seguro = preparar_sql_seguro(generar_sql(prompt, pregunta))
    except ValueError as exc:
        return ResultadoConsulta(
            respuesta=f"La consulta generada fue rechazada: {exc}",
            sql_generado=None,
            fuera_de_alcance=True,
        )

    filas = ejecutar_sql(sql_seguro)
    return ResultadoConsulta(
        respuesta=redactar_respuesta(pregunta, filas),
        sql_generado=sql_seguro,
        fuera_de_alcance=False,
    )