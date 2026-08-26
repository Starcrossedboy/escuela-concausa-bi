"""Guardarrailes de seguridad para el agente conversacional (US-304a).

Este modulo no ejecuta SQL ni depende del RAG de US-304b. Su responsabilidad es acotar la
pregunta y la consulta generada antes de que otra capa decida recuperar contexto o consultar Gold.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PALABRAS_AMBITO = frozenset(
    {
        "escuela",
        "escuelas",
        "matricula",
        "riesgo",
        "driver",
        "drivers",
        "municipio",
        "municipios",
        "entidad",
        "entidades",
        "pobreza",
        "rezago",
        "inseguridad",
        "delito",
        "delitos",
        "infraestructura",
        "conectividad",
        "agua",
        "aire",
        "calidad",
        "prediccion",
        "predicciones",
        "recomendacion",
        "recomendaciones",
        "cct",
        "ciclo",
        "faro",
    }
)

VERBOS_PROHIBIDOS = frozenset(
    {
        "alter",
        "create",
        "delete",
        "drop",
        "insert",
        "merge",
        "replace",
        "truncate",
        "update",
        "upsert",
        "vacuum",
    }
)

PATRON_PALABRA = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b")
PATRON_LIMIT = re.compile(r"\blimit\s+(\d+)\b", re.IGNORECASE)
PATRON_COMENTARIO = re.compile(r"(--|/\*|\*/)")
PATRON_REFERENCIA = re.compile(
    r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)",
    re.IGNORECASE,
)
PATRON_CTE = re.compile(
    r"(?:\bwith\b|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(",
    re.IGNORECASE,
)
PATRON_JOIN_COMA = re.compile(
    r"\bfrom\s+[a-zA-Z_][a-zA-Z0-9_.]*(?:\s+(?:as\s+)?[a-zA-Z_][a-zA-Z0-9_]*)?\s*,",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ResultadoGuardrail:
    """Resultado de aplicar una regla de seguridad."""

    permitido: bool
    razon: str | None = None


def pregunta_en_alcance(pregunta: str) -> ResultadoGuardrail:
    """Valida si una pregunta pertenece al dominio de FARO.

    La regla es deliberadamente conservadora: al menos una palabra debe pertenecer al vocabulario
    del proyecto. Carlos (US-304b) podra enriquecer esto con recuperacion semantica, pero este
    primer filtro evita que el agente intente responder temas ajenos.
    """
    tokens = {token.lower() for token in PATRON_PALABRA.findall(pregunta)}
    if tokens & PALABRAS_AMBITO:
        return ResultadoGuardrail(True)
    return ResultadoGuardrail(False, "Pregunta fuera del alcance de FARO.")


def validar_sql_lectura(sql: str) -> ResultadoGuardrail:
    """Permite solo SQL de lectura auditable sobre Gold.

    Rechaza comentarios, sentencias multiples y cualquier verbo de escritura o DDL. El agente debe
    producir una sola consulta `SELECT` o `WITH ... SELECT`.
    """
    consulta = sql.strip()
    if not consulta:
        return ResultadoGuardrail(False, "SQL vacio.")
    if PATRON_COMENTARIO.search(consulta):
        return ResultadoGuardrail(False, "SQL con comentarios no permitido.")
    if ";" in consulta.rstrip(";"):
        return ResultadoGuardrail(False, "SQL con multiples sentencias no permitido.")

    tokens = [token.lower() for token in PATRON_PALABRA.findall(consulta)]
    if not tokens:
        return ResultadoGuardrail(False, "SQL sin tokens validos.")
    if tokens[0] not in {"select", "with"}:
        return ResultadoGuardrail(False, "Solo se permiten consultas SELECT o WITH.")

    prohibidos = sorted(set(tokens) & VERBOS_PROHIBIDOS)
    if prohibidos:
        return ResultadoGuardrail(False, f"SQL contiene verbo prohibido: {', '.join(prohibidos)}.")
    if PATRON_JOIN_COMA.search(consulta):
        return ResultadoGuardrail(False, "SQL con unión por coma no permitido; usa JOIN explícito.")

    referencias = [referencia.lower() for referencia in PATRON_REFERENCIA.findall(consulta)]
    if not referencias:
        return ResultadoGuardrail(False, "SQL sin tabla de Gold.")
    ctes = {cte.lower() for cte in PATRON_CTE.findall(consulta)}
    fuera_de_gold = [
        referencia
        for referencia in referencias
        if not referencia.startswith("gold.") and referencia not in ctes
    ]
    if fuera_de_gold:
        return ResultadoGuardrail(
            False,
            f"SQL fuera del esquema Gold: {', '.join(sorted(set(fuera_de_gold)))}.",
        )
    return ResultadoGuardrail(True)


def aplicar_limit(sql: str, limite: int = 1000) -> str:
    """Garantiza un `LIMIT` maximo para respuestas auditables y acotadas."""
    consulta = sql.strip().rstrip(";")
    match = PATRON_LIMIT.search(consulta)
    if match:
        actual = int(match.group(1))
        if actual <= limite:
            return f"{consulta};"
        inicio, fin = match.span(1)
        return f"{consulta[:inicio]}{limite}{consulta[fin:]};"
    return f"{consulta} LIMIT {limite};"


def preparar_sql_seguro(sql: str, limite: int = 1000) -> str:
    """Valida y normaliza SQL de solo lectura.

    Raises:
        ValueError: si la consulta viola los guardarrailes.
    """
    resultado = validar_sql_lectura(sql)
    if not resultado.permitido:
        raise ValueError(resultado.razon)
    return aplicar_limit(sql, limite=limite)
