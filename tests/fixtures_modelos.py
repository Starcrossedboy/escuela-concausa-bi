"""Fake de `RepositorioModelos` para la suite rápida del contrato (US-412, cierra BUG-010).

Implementa `src.api.repositorio_modelos.RepositorioModelos` en memoria, 100% datos sintéticos. Se
inyecta en `tests/test_api_contract.py` vía `app.dependency_overrides[get_repositorio_modelos]`,
mismo patrón que `RepositorioGoldFake` (`tests/fixtures_gold.py`, US-411) -- sin Postgres, sin
SQLite (no modela `gold` igual que Postgres).

Mismos CCT que `ESCUELAS_FAKE` (`tests/fixtures_gold.py`) para que las pruebas de `/escuelas` y de
`/predicciones` sean consistentes entre sí sobre la misma escuela sintética.
"""

from __future__ import annotations

from copy import deepcopy

from src.api.repositorio_modelos import RepositorioModelosNoDisponible

PREDICCIONES_FAKE: list[dict] = [
    {
        "cct": "09DPR0001A",
        "id_ciclo": "2024-2025",
        "indice_riesgo": 0.72,
        "driver_dominante": "D2",
        "recomendacion": "Coordinar con seguridad pública rutas escolares seguras y entornos protegidos.",
        "mlflow_run_id": "fake-run-ml01-0001",
        "cluster": None,  # ML-03 sin productor (BUG-010, US-321)
    },
    {
        "cct": "19DES0007C",
        "id_ciclo": "2024-2025",
        "indice_riesgo": 0.31,
        "driver_dominante": "D4",
        "recomendacion": "Ampliar conectividad y dotación de equipo de cómputo.",
        "mlflow_run_id": "fake-run-ml01-0002",
        "cluster": None,
    },
]


class RepositorioModelosFake:
    """Mismo contrato que `RepositorioModelosPostgres`, resuelto en memoria."""

    def __init__(self) -> None:
        self._predicciones = deepcopy(PREDICCIONES_FAKE)

    def obtener_prediccion(self, cct: str, id_ciclo: str) -> dict | None:
        for p in self._predicciones:
            if p["cct"] == cct and p["id_ciclo"] == id_ciclo:
                return dict(p)
        return None

    def listar_predicciones(self, ccts: list[str], id_ciclo: str) -> list[dict]:
        return [
            dict(p) for p in self._predicciones if p["cct"] in ccts and p["id_ciclo"] == id_ciclo
        ]


class RepositorioModelosNoDisponibleFake:
    """Simula un Postgres que nunca responde a tiempo (US-416).

    Usado para probar el mapeo a 503 `service_unavailable` en `test_api_contract.py` sin tocar
    Postgres real -- mismo espíritu que `RepositorioModelosFake`, pero para el camino de error.
    """

    def obtener_prediccion(self, cct: str, id_ciclo: str) -> dict | None:
        raise RepositorioModelosNoDisponible("Postgres no respondió en 3000ms.")

    def listar_predicciones(self, ccts: list[str], id_ciclo: str) -> list[dict]:
        raise RepositorioModelosNoDisponible("Postgres no respondió en 3000ms.")
