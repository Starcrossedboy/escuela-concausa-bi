"""BUG-029 — un dataset roto no debe abortar el sync completo.

Historia: US-222 / US-205 / REQ-002 (Oscar Antonio Quiroz Lázaro, Célula 2).

Antes del fix, `ensure_datasets()` en `superset/sync_semantic_layer.py`
propagaba sin capturar cualquier excepción del POST/PUT de un dataset — un
solo 500 (tabla Gold ausente en un ambiente sin Bronze completo) abortaba
toda la corrida, incluidos los tableros alfabéticamente posteriores que sí
estaban sanos. `db09_cubo_recomendaciones` era el caso real documentado en
`vault/06_Quality_Testing/Bug_Register.md`, y `db10_cubo_pipeline` — que
viene después alfabéticamente — nunca se intentaba registrar.

Estas pruebas importan el módulo sin red (mismo patrón que
`tests/test_semantic_db01_db02.py`) y sustituyen `_request` por un doble
que falla a propósito en un dataset específico, para verificar que
`ensure_datasets()` reporta y continúa en vez de abortar.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def sync():
    """Importa superset/sync_semantic_layer.py como módulo (sin red en import)."""
    ruta = RAIZ / "superset" / "sync_semantic_layer.py"
    spec = importlib.util.spec_from_file_location("sync_semantic_layer_bug029", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("sync_semantic_layer_bug029", modulo)
    spec.loader.exec_module(modulo)
    return modulo


def test_un_dataset_roto_no_aborta_los_posteriores(sync, monkeypatch) -> None:
    """db09 falla (500 simulado) -> db10 (posterior alfabético) igual se registra."""
    creados: list[str] = []

    def _request_falso(method, path, token=None, body=None, csrf_token=None, **kw):
        if method == "GET" and path == "/api/v1/dataset/":
            return {"result": []}  # ningún dataset preexistente: todo va por POST
        if method == "POST" and path == "/api/v1/dataset/":
            nombre = body["table_name"]
            if nombre == "db09_cubo_recomendaciones":
                raise RuntimeError("HTTP 500: relation \"gold.recomendaciones\" does not exist")
            creados.append(nombre)
            return {"id": len(creados)}
        raise AssertionError(f"llamada inesperada: {method} {path}")

    monkeypatch.setattr(sync, "_request", _request_falso)

    datasets = sync.ensure_datasets(token="t", csrf="c", db_id=1)

    assert "db09_cubo_recomendaciones" not in datasets, (
        "el dataset roto no debe registrarse, pero tampoco debe tumbar el resto"
    )
    assert "db10_cubo_pipeline" in datasets, (
        "BUG-029: db10 viene después de db09 alfabéticamente — antes del fix, "
        "nunca se intentaba porque el sync ya había abortado en db09"
    )
    # El resto de los 16 .sql de superset/semantic/ tampoco debieron perderse.
    assert len(datasets) == len(list((RAIZ / "superset" / "semantic").glob("*.sql"))) - 1


def test_dataset_sano_no_se_ve_afectado_por_uno_roto(sync, monkeypatch) -> None:
    """DB-07 (antes de DB-09 alfabéticamente) sigue registrándose normal."""

    def _request_falso(method, path, token=None, body=None, csrf_token=None, **kw):
        if method == "GET" and path == "/api/v1/dataset/":
            return {"result": []}
        if method == "POST" and path == "/api/v1/dataset/":
            if body["table_name"] == "db09_cubo_recomendaciones":
                raise RuntimeError("HTTP 500")
            return {"id": 1}
        raise AssertionError(f"llamada inesperada: {method} {path}")

    monkeypatch.setattr(sync, "_request", _request_falso)

    datasets = sync.ensure_datasets(token="t", csrf="c", db_id=1)

    assert "db07_cubo_completitud" in datasets
    assert "db07_mapa_vacios" in datasets


def test_sin_datasets_rotos_nada_cambia(sync, monkeypatch) -> None:
    """Guardia de no-regresión: sin fallos, todos los .sql se registran igual que antes."""

    def _request_falso(method, path, token=None, body=None, csrf_token=None, **kw):
        if method == "GET" and path == "/api/v1/dataset/":
            return {"result": []}
        if method == "POST" and path == "/api/v1/dataset/":
            return {"id": 1}
        raise AssertionError(f"llamada inesperada: {method} {path}")

    monkeypatch.setattr(sync, "_request", _request_falso)

    datasets = sync.ensure_datasets(token="t", csrf="c", db_id=1)

    esperados = {p.stem for p in (RAIZ / "superset" / "semantic").glob("*.sql")}
    assert set(datasets.keys()) == esperados
