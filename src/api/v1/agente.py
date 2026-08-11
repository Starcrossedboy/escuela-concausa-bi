"""Agente conversacional `/agente/*` (§3.5).

Responde en lenguaje natural sobre Gold y devuelve el SQL generado para auditoría. **Nunca**
ejecuta escritura/borrado; rechaza preguntas fuera de alcance (`fuera_de_alcance: true`).
En el stub la respuesta es fija; la Célula 3 conecta el RAG real (Text-to-SQL).
"""
from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import AgenteConsultaIn, AgenteRespuestaOut

router = APIRouter(prefix="/agente", tags=["Agente"])

_PALABRAS_FUERA_ALCANCE = ("borrar", "elimina", "drop", "update", "delete")


@router.post("/consulta", response_model=AgenteRespuestaOut)
def consulta(body: AgenteConsultaIn) -> AgenteRespuestaOut:
    """Consulta en lenguaje natural sobre Gold (rol mínimo: ciudadano)."""
    pregunta = body.pregunta.lower()
    if any(p in pregunta for p in _PALABRAS_FUERA_ALCANCE):
        return AgenteRespuestaOut(
            respuesta="Esa operación no está permitida: el agente es de solo lectura.",
            sql_generado=None,
            fuera_de_alcance=True,
        )
    return AgenteRespuestaOut(
        respuesta="En el alcance actual hay 4 escuelas; 2 superan el umbral de riesgo (0.5).",
        sql_generado="SELECT cct, indice_riesgo FROM gold.features_escuela WHERE indice_riesgo >= 0.5;",
        fuera_de_alcance=False,
    )
