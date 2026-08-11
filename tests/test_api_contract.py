"""Pruebas del contrato de la API v1 (US-401).

Verifican que el stub cumple `03_Architecture/API_Specification.md`: rutas presentes, códigos
correctos (200/302/404/422), formas de respuesta (`Page`, `ErrorOut`) y que el OpenAPI publicado
en `api/openapi.v1.json` está sincronizado con el código.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.export_openapi import SALIDA
from src.api.app import API_PREFIX, app

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# --------------------------------------------------------------------------- #
# Salud / versión
# --------------------------------------------------------------------------- #


def test_health_ok(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_version_ok(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/version")
    assert r.status_code == 200
    assert r.json()["api"] == "v1"


# --------------------------------------------------------------------------- #
# Lectura sobre Gold
# --------------------------------------------------------------------------- #


def test_escuelas_devuelve_page(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/escuelas")
    assert r.status_code == 200
    cuerpo = r.json()
    assert {"items", "total", "page", "size"} <= cuerpo.keys()
    assert cuerpo["total"] == len(cuerpo["items"]) >= 1
    escuela = cuerpo["items"][0]
    assert len(escuela["cct"]) == 10
    assert len(escuela["cve_mun"]) == 5
    assert 0 <= escuela["indice_riesgo"] <= 1


def test_escuelas_filtro_por_entidad(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/escuelas", params={"cve_ent": "09"})
    assert r.status_code == 200
    assert all(e["cve_mun"].startswith("09") for e in r.json()["items"])


def test_escuela_detalle_incluye_drivers(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/escuelas/09DPR0001A")
    assert r.status_code == 200
    cuerpo = r.json()
    assert {"d1", "d2", "d3", "d4", "d5", "d6"} <= cuerpo.keys()
    assert 0 <= cuerpo["indice_completitud_drivers"] <= 1


def test_escuela_inexistente_404_con_forma_error(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/escuelas/00XXXX0000Z")
    assert r.status_code == 404
    cuerpo = r.json()
    assert cuerpo["error"] == "not_found"
    assert {"error", "message", "request_id"} == cuerpo.keys()
    # No se filtra detalle interno ni el CCT crudo.
    assert "Traceback" not in cuerpo["message"]


def test_municipio_ok_y_404(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/municipios/09010").status_code == 200
    assert client.get(f"{API_PREFIX}/municipios/00000").status_code == 404


def test_kpis_ok(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/kpis")
    assert r.status_code == 200
    assert r.json()["escuelas_en_riesgo"] >= 0


# --------------------------------------------------------------------------- #
# Predicciones
# --------------------------------------------------------------------------- #


def test_prediccion_combina_ml(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/predicciones/09DPR0001A")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["driver_dominante"].startswith("D")
    assert cuerpo["recomendacion"]  # ML-02 prescriptivo, no vacío
    assert isinstance(cuerpo["cluster"], int)  # ML-03


def test_prediccion_batch(client: TestClient) -> None:
    r = client.post(
        f"{API_PREFIX}/predicciones/batch",
        json={"ccts": ["09DPR0001A", "19DES0007C"], "id_ciclo": "2024-2025"},
    )
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_prediccion_batch_valida_entrada_422(client: TestClient) -> None:
    r = client.post(f"{API_PREFIX}/predicciones/batch", json={"ccts": [], "id_ciclo": "x"})
    assert r.status_code == 422
    assert r.json()["error"] == "validation_error"


# --------------------------------------------------------------------------- #
# Agente
# --------------------------------------------------------------------------- #


def test_agente_responde(client: TestClient) -> None:
    r = client.post(f"{API_PREFIX}/agente/consulta", json={"pregunta": "¿Cuántas escuelas en riesgo?"})
    assert r.status_code == 200
    assert r.json()["fuera_de_alcance"] is False


def test_agente_rechaza_escritura(client: TestClient) -> None:
    r = client.post(f"{API_PREFIX}/agente/consulta", json={"pregunta": "DROP table escuelas"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["fuera_de_alcance"] is True
    assert cuerpo["sql_generado"] is None


# --------------------------------------------------------------------------- #
# Auth (stub) y admin
# --------------------------------------------------------------------------- #


def test_auth_login_redirige(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/auth/login", follow_redirects=False)
    assert r.status_code == 302


def test_auth_me_devuelve_rol(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/auth/me")
    assert r.status_code == 200
    assert r.json()["role"] in ("ciudadano", "analista")


def test_admin_pipeline_run_202(client: TestClient) -> None:
    r = client.post(f"{API_PREFIX}/admin/pipeline/run", json={"dag": "bronze", "ciclo": "2024-2025"})
    assert r.status_code == 202
    assert r.json()["estado"] == "accepted"


# --------------------------------------------------------------------------- #
# OpenAPI publicado sincronizado con el código
# --------------------------------------------------------------------------- #


def test_openapi_publicado_existe_y_sincronizado(client: TestClient) -> None:
    """El JSON publicado debe estar estructuralmente sincronizado con el código.

    Se compara la **estructura** (rutas + métodos + nombres de modelos), no el JSON completo:
    así el test detecta "olvidé regenerar tras cambiar el contrato" sin volverse frágil ante
    diferencias menores del OpenAPI entre versiones de FastAPI (requirements usa pisos, no pines).
    """
    assert SALIDA.exists(), "Falta api/openapi.v1.json. Corre: python scripts/export_openapi.py"
    en_disco = json.loads(SALIDA.read_text(encoding="utf-8"))
    en_vivo = app.openapi()

    def rutas_y_metodos(spec: dict) -> set[str]:
        return {
            f"{metodo.upper()} {ruta}"
            for ruta, ops in spec.get("paths", {}).items()
            for metodo in ops
        }

    def modelos(spec: dict) -> set[str]:
        return set(spec.get("components", {}).get("schemas", {}).keys())

    assert rutas_y_metodos(en_disco) == rutas_y_metodos(en_vivo), (
        "Rutas del OpenAPI publicado desincronizadas. Regenéralo: python scripts/export_openapi.py"
    )
    assert modelos(en_disco) == modelos(en_vivo), (
        "Modelos del OpenAPI publicado desincronizados. Regenéralo: python scripts/export_openapi.py"
    )


def test_openapi_declara_todas_las_rutas(client: TestClient) -> None:
    paths = app.openapi()["paths"].keys()
    esperadas = [
        f"{API_PREFIX}/health",
        f"{API_PREFIX}/version",
        f"{API_PREFIX}/auth/login",
        f"{API_PREFIX}/escuelas",
        f"{API_PREFIX}/escuelas/{{cct}}",
        f"{API_PREFIX}/municipios",
        f"{API_PREFIX}/kpis",
        f"{API_PREFIX}/predicciones/{{cct}}",
        f"{API_PREFIX}/predicciones/batch",
        f"{API_PREFIX}/agente/consulta",
        f"{API_PREFIX}/admin/pipeline/run",
        f"{API_PREFIX}/admin/metrics",
    ]
    for ruta in esperadas:
        assert ruta in paths, f"Falta la ruta {ruta} en el OpenAPI"
