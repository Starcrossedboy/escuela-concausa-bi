"""Predicciones / inferencia ML: `/predicciones/*` (§3.4).

`PrediccionOut` combina ML-01 (riesgo), ML-02 (driver + recomendación) y ML-03 (cluster, `None`
hasta que exista -- ver BUG-010). La explicación SHAP completa y el batch son **solo analista**
(RBAC de US-403, no forzado aún en este stub).

`prediccion`/`prediccion_batch` leen `gold.predicciones` + `gold.recomendaciones` a través de
`RepositorioModelos` (`src/api/repositorio_modelos.py`, US-412) -- cierra BUG-010, que detectó que
seguían leyendo `src/api/mock_data.py` (un valor fabricado, no la salida de ningún modelo).
`explicacion` sigue sobre `mock_data` (SHAP no tiene fuente en Gold todavía; fuera de alcance de
BUG-010, que cubre solo `/predicciones` y `/predicciones/batch`).

Si Postgres no responde a tiempo (`RepositorioModelosNoDisponible`, US-416), ambas rutas devuelven
503 `service_unavailable` -- nunca dejan la excepción caer al handler genérico de `app.py` (que la
convertiría en un 500 `internal_error` menos específico) ni inventan una predicción.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api import mock_data
from src.api.repositorio_modelos import (
    RepositorioModelos,
    RepositorioModelosNoDisponible,
    get_repositorio_modelos,
)
from src.api.schemas import (
    ExplicacionSHAPOut,
    Page,
    PrediccionBatchIn,
    PrediccionOut,
)
from src.api.v1.common import paginate

router = APIRouter(prefix="/predicciones", tags=["Predicciones"])


def _buscar_escuela(cct: str) -> dict:
    for e in mock_data.ESCUELAS:
        if e["cct"] == cct:
            return e
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CCT inexistente o fuera de alcance.")


@router.get("/{cct}", response_model=PrediccionOut)
def prediccion(
    cct: str,
    ciclo: str = Query(mock_data.CICLO_DEFAULT),
    repo: RepositorioModelos = Depends(get_repositorio_modelos),
) -> PrediccionOut:
    """Riesgo y driver dominante de una escuela (rol mínimo: ciudadano)."""
    try:
        fila = repo.obtener_prediccion(cct, ciclo)
    except RepositorioModelosNoDisponible as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="Servicio de predicciones no disponible."
        ) from exc
    if fila is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="CCT sin predicción o fuera de alcance."
        )
    return PrediccionOut(**fila)


@router.post("/batch", response_model=Page[PrediccionOut])
def prediccion_batch(
    body: PrediccionBatchIn,
    repo: RepositorioModelos = Depends(get_repositorio_modelos),
) -> Page[PrediccionOut]:
    """Inferencia en lote (rol mínimo: **analista** — se forzará en US-403).

    Omite silenciosamente los CCT sin fila en `gold.predicciones` -- nunca inventa una
    predicción para un CCT fuera de alcance o sin modelo corrido.
    """
    try:
        filas = repo.listar_predicciones(body.ccts, body.id_ciclo)
    except RepositorioModelosNoDisponible as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="Servicio de predicciones no disponible."
        ) from exc
    items = [PrediccionOut(**fila) for fila in filas]
    return paginate(items, page=1, size=100)


@router.get("/{cct}/explicacion", response_model=ExplicacionSHAPOut)
def explicacion(cct: str) -> ExplicacionSHAPOut:
    """Explicación SHAP completa (rol mínimo: **analista** — se forzará en US-403)."""
    escuela = _buscar_escuela(cct)
    contribuciones = {
        f"D{i}": (escuela.get(f"d{i}") or 0.0) for i in range(1, 7)
    }
    return ExplicacionSHAPOut(
        cct=escuela["cct"],
        driver_dominante=escuela["driver_dominante"],
        contribuciones=contribuciones,
    )
