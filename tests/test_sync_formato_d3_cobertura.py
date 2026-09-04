"""Un `formato:` de metrics_*.yaml sin entrada en FORMATO_D3 rompe el sync en silencio.

Historia: US-223 (Oscar Antonio Quiroz Lázaro, Célula 2).

`_apply_metrics_and_columns()` construye `d3format` con
`FORMATO_D3.get(m.get("formato", ""), "")` — si el `formato:` de una métrica no está en
el diccionario, `d3format` cae a cadena vacía. Superset exige `d3format` de 1 a 128
caracteres, así que el PUT del dataset entero falla con HTTP 422 — y como es un solo
PUT con todas las métricas, **ninguna métrica del dataset se aplica**, no solo la del
formato faltante. Así se descubrió: `metrics_db10.yaml` usa `formato: fecha` (única
métrica de fecha del proyecto) para `ultima_ingesta`, `FORMATO_D3` no tenía esa clave, y
las 4 métricas de `db10_cubo_pipeline` (DB-10) quedaron sin aplicar — los 5 charts del
tablero mostraban "Metric 'filas' does not exist" pese a que el dataset y los charts sí
se habían creado.

Estas pruebas importan el módulo sin red (mismo patrón que
`tests/test_sync_resiliencia_bug029.py`) y verifican que todo `formato:` realmente usado
en el repo tiene su entrada — para que un formato nuevo sin mapear truene aquí, no en
silencio contra Superset real.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
SEMANTIC_DIR = RAIZ / "superset" / "semantic"


@pytest.fixture(scope="module")
def sync():
    """Importa superset/sync_semantic_layer.py como módulo (sin red en import)."""
    ruta = RAIZ / "superset" / "sync_semantic_layer.py"
    spec = importlib.util.spec_from_file_location("sync_semantic_layer_d3format", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("sync_semantic_layer_d3format", modulo)
    spec.loader.exec_module(modulo)
    return modulo


def _formatos_usados() -> set[str]:
    """Todo valor de `formato:` que aparece en algún metrics_*.yaml del repo."""
    formatos: set[str] = set()
    for archivo in SEMANTIC_DIR.glob("metrics_*.yaml"):
        data = yaml.safe_load(archivo.read_text(encoding="utf-8"))
        for ds in data.get("datasets", []):
            for metrica in ds.get("metricas", []):
                if "formato" in metrica:
                    formatos.add(metrica["formato"])
    return formatos


def test_fecha_esta_mapeado(sync) -> None:
    """Regresión directa: 'fecha' -> un d3-time-format real, no cadena vacía.

    'smart_date' (el sentinel de Superset para ejes de serie de tiempo) se probó
    primero pero en un big_number_total interpreta el timestamp como número crudo
    en vez de fecha -- ver el comentario en FORMATO_D3.
    """
    assert sync.FORMATO_D3.get("fecha") == "%Y-%m-%d"


def test_ningun_formato_produce_d3format_vacio(sync) -> None:
    """Ningún valor de FORMATO_D3 debe ser cadena vacía (Superset exige 1-128 chars)."""
    for formato, d3 in sync.FORMATO_D3.items():
        assert d3, f"FORMATO_D3['{formato}'] es cadena vacía -- Superset lo rechazaría"


def test_todo_formato_usado_en_el_repo_esta_mapeado(sync) -> None:
    """Guarda de no-regresión: cada `formato:` de cada metrics_*.yaml tiene entrada.

    Si alguien agrega un metrics_*.yaml nuevo con un `formato:` sin mapear, esta prueba
    truena aquí -- en vez de que el dataset entero pierda sus métricas en silencio.
    """
    usados = _formatos_usados()
    assert usados, "no se encontraron metrics_*.yaml -- revisa SEMANTIC_DIR"
    sin_mapear = usados - set(sync.FORMATO_D3)
    assert not sin_mapear, (
        f"formato(s) sin entrada en FORMATO_D3: {sorted(sin_mapear)} -- "
        "agrégalos en superset/sync_semantic_layer.py o el PUT del dataset fallará"
    )
