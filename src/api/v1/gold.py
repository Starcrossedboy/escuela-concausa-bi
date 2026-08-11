"""Lectura sobre Gold: `/escuelas`, `/municipios`, `/kpis` (§3.3).

Solo lectura (todos los `GET`). Fuera de `SCOPE_ENTIDADES` → lista vacía o 404, nunca datos
de otra entidad. En el stub los datos vienen de `mock_data`; al llegar Gold real (Célula 1) se
sustituyen por consultas sin cambiar las formas.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from src.api import mock_data
from src.api.schemas import (
    EscuelaDetalleOut,
    EscuelaOut,
    KpisOut,
    MunicipioOut,
    Page,
)
from src.api.v1.common import paginate

router = APIRouter(tags=["Gold"])


@router.get("/escuelas", response_model=Page[EscuelaOut])
def listar_escuelas(
    cve_ent: str | None = Query(None, min_length=2, max_length=2),
    cve_mun: str | None = Query(None, min_length=5, max_length=5),
    nivel: str | None = Query(None),
    ciclo: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
) -> Page[EscuelaOut]:
    """Lista escuelas de Gold con filtros opcionales y paginación (rol mínimo: ciudadano)."""
    filas = mock_data.ESCUELAS
    if cve_ent:
        filas = [e for e in filas if e["cve_mun"].startswith(cve_ent)]
    if cve_mun:
        filas = [e for e in filas if e["cve_mun"] == cve_mun]
    if nivel:
        filas = [e for e in filas if e["nivel"].upper() == nivel.upper()]
    items = [EscuelaOut(**e) for e in filas]
    return paginate(items, page, size)


@router.get("/escuelas/{cct}", response_model=EscuelaDetalleOut)
def obtener_escuela(cct: str) -> EscuelaDetalleOut:
    """Detalle de una escuela por CCT, con los 6 drivers (None => SIN_DATO)."""
    for e in mock_data.ESCUELAS:
        if e["cct"] == cct:
            return EscuelaDetalleOut(**e)
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CCT inexistente o fuera de alcance.")


@router.get("/municipios", response_model=Page[MunicipioOut])
def listar_municipios(
    cve_ent: str | None = Query(None, min_length=2, max_length=2),
    ciclo: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
) -> Page[MunicipioOut]:
    """Lista municipios de Gold con filtros opcionales y paginación (rol mínimo: ciudadano)."""
    filas = mock_data.MUNICIPIOS
    if cve_ent:
        filas = [m for m in filas if m["cve_mun"].startswith(cve_ent)]
    items = [MunicipioOut(**m) for m in filas]
    return paginate(items, page, size)


@router.get("/municipios/{cve_mun}", response_model=MunicipioOut)
def obtener_municipio(cve_mun: str) -> MunicipioOut:
    """Detalle de un municipio por clave INEGI de 5 dígitos."""
    for m in mock_data.MUNICIPIOS:
        if m["cve_mun"] == cve_mun:
            return MunicipioOut(**m)
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Municipio inexistente o fuera de alcance.")


@router.get("/kpis", response_model=KpisOut)
def obtener_kpis(
    cve_ent: str | None = Query(None, min_length=2, max_length=2),
    cve_mun: str | None = Query(None, min_length=5, max_length=5),
    ciclo: str | None = Query(None),
) -> KpisOut:
    """KPIs agregados del tablero (rol mínimo: ciudadano)."""
    return KpisOut(**mock_data.kpis_mock())
