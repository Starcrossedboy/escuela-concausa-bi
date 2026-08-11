"""Administración `/admin/*` — solo `analista` (§3.6).

RBAC no forzado en este stub (US-403). El agente y los endpoints de datos **nunca** ejecutan
escritura/borrado; `pipeline/run` solo encola un DAG (respuesta 202 accepted en el contrato).
"""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from src.api import mock_data
from src.api.schemas import MetricsOut, PipelineRunIn, PipelineRunOut

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.post("/pipeline/run", response_model=PipelineRunOut, status_code=status.HTTP_202_ACCEPTED)
def pipeline_run(body: PipelineRunIn) -> PipelineRunOut:
    """Encola una corrida de pipeline (rol: **analista**). Devuelve 202 accepted."""
    return PipelineRunOut(run_id=f"run-{body.dag}-{body.ciclo}", estado="accepted")


@router.get("/export")
def export(
    tabla: str = Query(...),
    ciclo: str | None = Query(None),
    formato: str = Query("csv"),
) -> dict:
    """Exporta datos en bruto (rol: **analista**). En el stub devuelve una referencia, no el stream."""
    return {
        "tabla": tabla,
        "ciclo": ciclo,
        "formato": formato,
        "url": f"gs://faro-exports/{tabla}.{formato}",
    }


@router.get("/metrics", response_model=MetricsOut)
def metrics() -> MetricsOut:
    """Métricas internas (rol: **analista**): frescura por fuente y estado de suites GE."""
    return MetricsOut(**mock_data.metrics_mock())
