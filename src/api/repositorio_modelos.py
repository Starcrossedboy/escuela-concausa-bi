"""Repositorio de datos para `/predicciones/{cct}` y `/predicciones/batch` (US-412, cierra BUG-010).

`src/api/v1/predicciones.py` leía `src/api/mock_data.py` -- un valor fabricado a mano, no la salida
de ningún modelo (BUG-010, `06_Quality_Testing/Bug_Register.md`). `gold.predicciones` y
`gold.recomendaciones` ya están pobladas y verificadas contra Postgres (US-313, Héctor Morales):
el swap es leerlas, no invocar MLflow en cada request. `mlflow_run_id` viaja en la fila y conserva
el enlace auditable a la corrida que produjo el valor -- "3 modelos integrados vía API" (REQ-003)
no se debilita por leer la tabla precalculada en vez de invocar el modelo en vivo.

Mismo patrón `Depends` + Protocol que `RepositorioGold` (`src/api/repositorio_gold.py`, US-411):
los endpoints dependen de una abstracción, no de Postgres directo, así que la suite rápida del
contrato la sustituye por un fake en memoria (`tests/fixtures_modelos.py`) sin necesitar Postgres.

`cluster` (ML-03) no tiene productor todavía -- US-321 (Estefany Hernández) sin entregar. Se
declara explícitamente `None` en vez de inventar un entero, mismo criterio SIN_DATO que
`EscuelaOut.indice_riesgo`. Ver `src/api/schemas.py::PrediccionOut.cluster` y BUG-010.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.engine import Engine

from src.api.db import get_engine, get_tablas

MODELO_ML01 = "ML-01"
GRANO_ESCUELA = "escuela"


class RepositorioModelos(Protocol):
    """Lecturas sobre `gold.predicciones` + `gold.recomendaciones` que necesita `/predicciones/*`."""

    def obtener_prediccion(self, cct: str, id_ciclo: str) -> dict | None:
        """Predicción de una escuela × ciclo, o `None` si no hay fila en `gold.predicciones`."""
        ...

    def listar_predicciones(self, ccts: list[str], id_ciclo: str) -> list[dict]:
        """Predicciones de una lista de CCT para un ciclo. Omite los CCT sin fila -- nunca
        inventa una predicción para un CCT que `gold.predicciones` no cubre."""
        ...


class RepositorioModelosPostgres:
    """Implementación real sobre `gold.predicciones` × `gold.recomendaciones` vía SQLAlchemy Core
    (mismo estilo que `RepositorioGoldPostgres`)."""

    def __init__(self, engine: Engine | None = None) -> None:
        self._engine = engine or get_engine()
        (_, _, _, _, self._predicciones, self._recomendaciones) = get_tablas()

    def _seleccion_prediccion(self):
        predicciones, recomendaciones = self._predicciones, self._recomendaciones
        return (
            select(
                predicciones.c.cct,
                predicciones.c.id_ciclo,
                predicciones.c.indice_riesgo,
                predicciones.c.mlflow_run_id,
                recomendaciones.c.driver_dominante,
                recomendaciones.c.recomendacion,
            )
            .select_from(
                predicciones.join(
                    recomendaciones,
                    (predicciones.c.cct == recomendaciones.c.cct)
                    & (predicciones.c.id_ciclo == recomendaciones.c.id_ciclo),
                )
            )
            .where(predicciones.c.modelo == MODELO_ML01)
            .where(predicciones.c.grano == GRANO_ESCUELA)
        )

    @staticmethod
    def _fila_a_dict(fila) -> dict:
        datos = dict(fila)
        datos["cluster"] = None  # ML-03 sin productor (BUG-010, US-321)
        return datos

    def obtener_prediccion(self, cct: str, id_ciclo: str) -> dict | None:
        consulta = self._seleccion_prediccion().where(
            self._predicciones.c.cct == cct, self._predicciones.c.id_ciclo == id_ciclo
        )
        with self._engine.connect() as conexion:
            fila = conexion.execute(consulta).mappings().first()
        return self._fila_a_dict(fila) if fila is not None else None

    def listar_predicciones(self, ccts: list[str], id_ciclo: str) -> list[dict]:
        if not ccts:
            return []
        consulta = self._seleccion_prediccion().where(
            self._predicciones.c.cct.in_(ccts), self._predicciones.c.id_ciclo == id_ciclo
        )
        with self._engine.connect() as conexion:
            filas = conexion.execute(consulta).mappings().all()
        return [self._fila_a_dict(fila) for fila in filas]


def get_repositorio_modelos() -> RepositorioModelos:
    """Dependencia de FastAPI (`Depends(get_repositorio_modelos)`). Las pruebas rápidas la
    sustituyen con `app.dependency_overrides[get_repositorio_modelos] = ...`
    (ver `tests/fixtures_modelos.py`) -- nunca con SQLite, mismo motivo que `RepositorioGold`."""
    return RepositorioModelosPostgres()
