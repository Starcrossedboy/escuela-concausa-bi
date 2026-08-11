"""Predicciones / inferencia ML: `/predicciones/*` (§3.4).

`PrediccionOut` combina ML-01 (riesgo), ML-02 (driver + recomendación) y ML-03 (cluster).
La explicación SHAP completa y el batch son **solo analista** (RBAC de US-403, no forzado aún
en este stub). Los valores provienen de `mock_data`; al integrar MLflow (Célula 3) es un *swap*.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from src.api import mock_data
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
def prediccion(cct: str, ciclo: str = Query(mock_data.CICLO_DEFAULT)) -> PrediccionOut:
    """Riesgo y driver dominante de una escuela (rol mínimo: ciudadano)."""
    escuela = _buscar_escuela(cct)
    return PrediccionOut(**mock_data.prediccion_de_escuela(escuela, ciclo))


@router.post("/batch", response_model=Page[PrediccionOut])
def prediccion_batch(body: PrediccionBatchIn) -> Page[PrediccionOut]:
    """Inferencia en lote (rol mínimo: **analista** — se forzará en US-403)."""
    items: list[PrediccionOut] = []
    for cct in body.ccts:
        for e in mock_data.ESCUELAS:
            if e["cct"] == cct:
                items.append(
                    PrediccionOut(**mock_data.prediccion_de_escuela(e, body.id_ciclo))
                )
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
