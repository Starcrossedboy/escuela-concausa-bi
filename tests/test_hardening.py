"""Pruebas del hardening de la API (US-404): CORS, rate limiting, validación estricta y errores
sin fuga de información interna.

Offline y sin BD: los 401/403/422/429 y las cabeceras CORS se resuelven antes o alrededor del
cuerpo del endpoint.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

import src.api.app as appmod
from src.api.app import API_PREFIX, app
from src.api.config import Settings
from src.api.repositorio_gold import get_repositorio_gold

# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #


def test_cors_permite_origen_configurado() -> None:
    client = TestClient(app)
    r = client.get(
        f"{API_PREFIX}/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_preflight_options() -> None:
    client = TestClient(app)
    r = client.options(
        f"{API_PREFIX}/escuelas",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


# --------------------------------------------------------------------------- #
# Rate limiting (motor `limits` -> ErrorOut 429)
# --------------------------------------------------------------------------- #


def test_rate_limit_devuelve_429_con_forma_error(monkeypatch) -> None:
    """Con un límite bajo, la petición que lo excede recibe 429 con la forma ErrorOut."""
    monkeypatch.setattr(
        appmod,
        "get_settings",
        lambda: Settings(rate_limit_default="2/minute", rate_limit_enabled=True, cors_origins=""),
    )
    fresh = appmod.create_app()
    client = TestClient(fresh)

    assert client.get(f"{API_PREFIX}/health").status_code == 200
    assert client.get(f"{API_PREFIX}/health").status_code == 200
    r = client.get(f"{API_PREFIX}/health")
    assert r.status_code == 429
    cuerpo = r.json()
    assert cuerpo["error"] == "rate_limited"
    assert {"error", "message", "request_id"} == cuerpo.keys()


def test_rate_limit_desactivado_no_limita(monkeypatch) -> None:
    monkeypatch.setattr(
        appmod,
        "get_settings",
        lambda: Settings(rate_limit_default="1/minute", rate_limit_enabled=False, cors_origins=""),
    )
    fresh = appmod.create_app()
    client = TestClient(fresh)
    for _ in range(5):
        assert client.get(f"{API_PREFIX}/health").status_code == 200


# --------------------------------------------------------------------------- #
# Validación estricta (extra="forbid")
# --------------------------------------------------------------------------- #


def test_campo_desconocido_en_body_da_422() -> None:
    client = TestClient(app)
    r = client.post(
        f"{API_PREFIX}/agente/consulta",
        json={"pregunta": "¿cuántas escuelas hay?", "inject": "rm -rf"},
    )
    assert r.status_code == 422
    assert r.json()["error"] == "validation_error"


def test_body_valido_sin_extras_no_es_422() -> None:
    client = TestClient(app)
    r = client.post(f"{API_PREFIX}/agente/consulta", json={"pregunta": "escuelas en riesgo"})
    assert r.status_code == 200


# --------------------------------------------------------------------------- #
# Errores sin fuga de información interna
# --------------------------------------------------------------------------- #


def test_error_interno_no_filtra_detalle() -> None:
    """Un fallo inesperado en una dependencia devuelve 500 genérico, sin traza ni el mensaje real."""

    class RepoExplota:
        def __getattr__(self, _name):
            raise RuntimeError("detalle interno secreto: DSN=postgres://user:pass@host/db")

    app.dependency_overrides[get_repositorio_gold] = lambda: RepoExplota()
    try:
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get(f"{API_PREFIX}/escuelas")
        assert r.status_code == 500
        cuerpo = r.json()
        assert cuerpo["error"] == "internal_error"
        assert "secreto" not in cuerpo["message"].lower()
        assert "postgres://" not in cuerpo["message"]
        assert "Traceback" not in cuerpo["message"]
    finally:
        app.dependency_overrides.clear()
