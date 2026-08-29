"""Prueba de BUG-008.

Verifica que la aplicacion configurada en docker/api.Dockerfile
expone las rutas del contrato v1.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOCKERFILE = RAIZ / "docker" / "api.Dockerfile"

# Rutas oficiales del contrato v1, copiadas literal de la lista "esperadas"
# en tests/test_api_contract.py::test_openapi_declara_todas_las_rutas.
# No se inventan aqui: es la misma fuente de verdad que ya usa el repo.
API_PREFIX = "/api/v1"
RUTAS_CONTRATO_V1 = [
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


def _extraer_app_del_cmd(texto_dockerfile: str) -> str:
    """Extrae la referencia modulo:atributo declarada en el CMD de uvicorn.

    Ejemplo: 'CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}'
    devuelve 'src.api.main:app'.
    """
    coincidencia = re.search(r"CMD\s+uvicorn\s+([\w\.]+:\w+)", texto_dockerfile)
    assert coincidencia, "No se encontro una referencia modulo:app en el CMD de uvicorn"
    return coincidencia.group(1)


def _importar_app(referencia: str):
    """Importa dinamicamente la app FastAPI que el Dockerfile declara arrancar."""
    modulo_nombre, atributo = referencia.split(":")
    modulo = importlib.import_module(modulo_nombre)
    return getattr(modulo, atributo)


def test_dockerfile_declara_un_cmd_uvicorn() -> None:
    """BUG-008: el Dockerfile debe declarar un CMD de uvicorn."""
    contenido = DOCKERFILE.read_text(encoding="utf-8")
    assert "CMD uvicorn" in contenido


def test_referencia_del_cmd_es_extraible() -> None:
    """El CMD debe declarar una referencia valida modulo:atributo."""
    contenido = DOCKERFILE.read_text(encoding="utf-8")
    referencia = _extraer_app_del_cmd(contenido)
    assert ":" in referencia


def test_app_que_arranca_el_contenedor_expone_el_contrato_v1() -> None:
    """BUG-008: la app que el Dockerfile arranca debe exponer el contrato v1.

    Este es el corazon del bug: hoy el CMD apunta a 'src.api.main:app' (el
    hola-mundo de 3 rutas), no a 'src.api.app:app' (el contrato real con 18
    rutas bajo /api/v1). Esta prueba falla mientras el Dockerfile no arranque
    la app correcta, y protege contra que el bug regrese en el futuro.

    Las rutas esperadas son las mismas que ya valida
    tests/test_api_contract.py::test_openapi_declara_todas_las_rutas, para no
    duplicar criterio propio y quedar trazada a la fuente oficial del contrato.
    """
    contenido = DOCKERFILE.read_text(encoding="utf-8")
    referencia = _extraer_app_del_cmd(contenido)
    app = _importar_app(referencia)

    rutas_expuestas = set(app.openapi()["paths"].keys())

    faltantes = [ruta for ruta in RUTAS_CONTRATO_V1 if ruta not in rutas_expuestas]

    assert not faltantes, (
        f"El Dockerfile arranca '{referencia}', que NO expone el contrato v1. "
        f"Faltan {len(faltantes)} de {len(RUTAS_CONTRATO_V1)} rutas: {faltantes}. "
        "El CMD debe apuntar a 'src.api.app:app' (BUG-008)."
    )
