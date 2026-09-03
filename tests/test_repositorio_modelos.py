"""Regresión de `RepositorioModelosPostgres` — degradación ante Gold inalcanzable o ausente (US-416).

`_con_timeout` capturaba solo `OperationalError` (timeout de Postgres). Un `ProgrammingError`
—esquema/tabla `gold.*` inexistente en el despliegue, caso real mientras la publicación de ML no
haya corrido contra esa base— se escapaba al handler genérico de `src/api/app.py` y se convertía
en un **500**. Ahora cualquier `SQLAlchemyError` se traduce a `RepositorioModelosNoDisponible`
(→ 503 `service_unavailable` uniforme). Se prueba sin Postgres: un `Engine` falso cuyo `begin()`
entrega una conexión que revienta al ejecutar.
"""

from __future__ import annotations

from typing import Self

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError

from src.api.repositorio_modelos import (
    RepositorioModelosNoDisponible,
    RepositorioModelosPostgres,
)


class _ConexionQueRevienta:
    """Conexión falsa: la primera `execute` (el `SET LOCAL`) lanza `error`."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False

    def execute(self, *_args: object, **_kwargs: object) -> None:
        raise self._error


class _EngineFalso:
    """`Engine` mínimo: `begin()` devuelve una conexión que revienta al ejecutar."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def begin(self) -> _ConexionQueRevienta:
        return _ConexionQueRevienta(self._error)


def _error_sqlalchemy(clase: type) -> Exception:
    # Firma de DBAPIError: (statement, params, orig)
    return clase("SELECT 1", {}, Exception("relation \"gold.predicciones\" does not exist"))


@pytest.mark.parametrize("clase_error", [ProgrammingError, OperationalError])
def test_con_timeout_traduce_cualquier_error_sqlalchemy(clase_error: type) -> None:
    """Timeout (`OperationalError`) y esquema ausente (`ProgrammingError`) → mismo 503."""
    repo = RepositorioModelosPostgres(engine=_EngineFalso(_error_sqlalchemy(clase_error)))

    with pytest.raises(RepositorioModelosNoDisponible):
        repo.obtener_prediccion("09DPR0001A", "2024-2025")

    with pytest.raises(RepositorioModelosNoDisponible):
        repo.listar_predicciones(["09DPR0001A"], "2024-2025")


def test_con_timeout_no_deja_escapar_la_excepcion_cruda() -> None:
    """La `ProgrammingError` original queda como causa, nunca se propaga tal cual."""
    repo = RepositorioModelosPostgres(engine=_EngineFalso(_error_sqlalchemy(ProgrammingError)))

    with pytest.raises(RepositorioModelosNoDisponible) as exc_info:
        repo.obtener_prediccion("09DPR0001A", "2024-2025")

    assert isinstance(exc_info.value.__cause__, ProgrammingError)


def test_listar_predicciones_vacio_no_toca_el_engine() -> None:
    """Lista vacía de CCT: cortocircuito antes de abrir transacción (no revienta)."""
    repo = RepositorioModelosPostgres(engine=_EngineFalso(_error_sqlalchemy(ProgrammingError)))
    assert repo.listar_predicciones([], "2024-2025") == []
