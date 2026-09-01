"""Ejecutor de SQL **de solo lectura** sobre el esquema Gold para el agente (US-404 / BUG-025).

Implementa la colaboración `ejecutar_sql` del seam del agente (`src/api/v1/agente.py`): recibe SQL ya
validado por `preparar_sql_seguro()` (Célula 3) y lo ejecuta contra Gold.

**Defensa en profundidad (capas independientes):**
1. Rol de PostgreSQL con **solo `SELECT` sobre `gold.*`** (DSN `DATABASE_URL_READ_ONLY`, provisto por
   Célula 5 en Secret Manager). Es la barrera real: aunque todo lo demás fallara, la BD rechaza escritura.
2. `SET TRANSACTION READ ONLY` en cada conexión.
3. `statement_timeout` para acotar consultas largas.
4. Revalidación con `validar_sql_lectura()` antes de tocar la BD (redundante con el rol, a propósito).

La configuración se lee del patrón `Settings` (`config.py`), **nunca** con `os.getenv()` suelto.
La conexión real solo existe donde `DATABASE_URL_READ_ONLY` esté definida; en local/CI está vacía y el
ejecutor no se cablea (el agente degrada seguro). Las pruebas de integración contra Postgres real
viven en US-422 (Eloisa).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from src.agente.guardrails import validar_sql_lectura
from src.api.config import get_settings


@lru_cache(maxsize=1)
def _engine_read_only() -> Engine:
    """Engine (cacheado) hacia el rol read-only. Lanza RuntimeError si no está configurado."""
    settings = get_settings()
    if not settings.database_url_read_only:
        raise RuntimeError(
            "DATABASE_URL_READ_ONLY no está configurado: el ejecutor SQL del agente no está "
            "disponible en este entorno."
        )
    return create_engine(
        settings.database_url_read_only,
        pool_pre_ping=True,
        connect_args={"options": f"-c statement_timeout={settings.agente_sql_timeout_ms}"},
    )


def ejecutar_sql_read_only(sql: str) -> list[dict[str, Any]]:
    """Ejecuta SQL de solo lectura sobre Gold y devuelve las filas como lista de dicts.

    Args:
        sql: consulta ya validada por `preparar_sql_seguro()` (SELECT/WITH sobre `gold.*` con LIMIT).

    Returns:
        Filas como `list[dict]` (puede ser vacía).

    Raises:
        ValueError: si el SQL no es de solo lectura sobre Gold (defensa en profundidad).
        RuntimeError: si el ejecutor no está configurado o la consulta falla.
    """
    verificacion = validar_sql_lectura(sql)
    if not verificacion.permitido:
        # No debería ocurrir si vino de preparar_sql_seguro(); es una barrera redundante.
        raise ValueError(f"SQL rechazado por el ejecutor read-only: {verificacion.razon}")

    engine = _engine_read_only()  # RuntimeError si falta configuración
    try:
        with engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            resultado = conn.execute(text(sql))
            return [dict(fila._mapping) for fila in resultado]
    except SQLAlchemyError as exc:
        # No se filtra el detalle real (DSN, SQL): el endpoint ya degrada a mensaje genérico.
        raise RuntimeError("No se pudo ejecutar la consulta read-only sobre Gold.") from exc
