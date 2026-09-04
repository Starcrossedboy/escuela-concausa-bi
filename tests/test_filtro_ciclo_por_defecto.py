"""Guarda del filtro de ciclo con valor por defecto en DB-03 y DB-04 (US-214a).

El defecto que estas pruebas impiden que vuelva es **invisible**: un filtro nativo sin
valor inicial deja el tablero sin filtrar al abrirlo, y cualquier tarjeta que agregue
sobre un cubo con varios ciclos suma TODOS los ciclos. En DB-03/DB-04 eso pintaba
**32 312 alumnos donde el ciclo 2024-2025 tiene 11 828** — 2.7x inflado. No hay error
en el sync, ni en la API, ni en la consola del navegador: solo un numero creible que
significa otra cosa.

Es el mismo defecto que Luis Tellez reporto el 2026-09-04 sobre `/api/v1/kpis` en
produccion (20 638 574 contra ~6.7M reales). Alla se corrigio en la API; los tableros
**no pasan por la API** —leen la base directo— asi que necesitan su propio arreglo y su
propia guarda.

Cubre dos clases de error, no dos instancias:

1. Un tablero cuyo cubo tiene grano multi-ciclo publica tarjetas agregadas sin fijar
   un ciclo por defecto.
2. `valor_por_defecto` deja de traducirse al `defaultDataMask` que Superset entiende,
   o su presencia cambia el comportamiento de los tableros que NO lo declaran
   (compatibilidad hacia atras: `sync_semantic_layer.py` es herramienta compartida de
   la Celula 2, la usan tambien DB-01/02/05/06/07/08/09/10).

Validacion estatica: no necesita Superset ni base de datos.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
DASHBOARDS = RAIZ / "superset" / "dashboards"

# Tableros de esta historia cuyo cubo tiene `id_ciclo` en el grano.
TABLEROS_MULTICICLO = {
    "DB-03": DASHBOARDS / "db03_ficha_escuela.yaml",
    "DB-04": DASHBOARDS / "db04_comparador_municipio.yaml",
}

# Un `big_number_total` es una sola cifra sin dimension: si el cubo trae varios ciclos y
# nadie filtro, esa cifra es la suma de todos. Son las que el defecto vuelve mentirosas.
VIZ_AGREGADO_SIN_DIMENSION = "big_number_total"


@pytest.fixture(scope="module")
def yaml_mod():
    return pytest.importorskip("yaml", reason="pyyaml no esta en requirements.txt")


@pytest.fixture(scope="module")
def sync():
    """Importa superset/sync_semantic_layer.py como modulo (sin red en import).

    Mismo patron que `test_sync_resiliencia_bug029.py`.
    """
    ruta = RAIZ / "superset" / "sync_semantic_layer.py"
    spec = importlib.util.spec_from_file_location("sync_semantic_layer_filtro_ciclo", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("sync_semantic_layer_filtro_ciclo", modulo)
    spec.loader.exec_module(modulo)
    return modulo


def _dashboard(yaml_mod, ruta: Path) -> dict:
    return yaml_mod.safe_load(ruta.read_text(encoding="utf-8"))["dashboards"][0]


# --------------------------------------------------------- clase 1: el tablero


@pytest.mark.parametrize("nombre", sorted(TABLEROS_MULTICICLO))
def test_el_filtro_de_ciclo_fija_un_valor_por_defecto(nombre: str, yaml_mod) -> None:
    """Sin valor inicial, las tarjetas suman todos los ciclos y nadie se entera."""
    cfg = _dashboard(yaml_mod, TABLEROS_MULTICICLO[nombre])
    ciclo = [f for f in cfg["filtros_globales"] if f["columna"] == "id_ciclo"]
    assert ciclo, f"{nombre}: perdio el filtro global de ciclo (AC-002.2)."
    assert ciclo[0].get("valor_por_defecto"), (
        f"{nombre}: el filtro de ciclo no fija `valor_por_defecto`. Al abrir el tablero "
        "nadie ha filtrado, asi que toda tarjeta agregada suma los ciclos que haya en el "
        "cubo — el defecto de 32 312 contra 11 828."
    )


@pytest.mark.parametrize("nombre", sorted(TABLEROS_MULTICICLO))
def test_toda_tarjeta_agregada_queda_cubierta_por_el_ciclo_por_defecto(
    nombre: str, yaml_mod
) -> None:
    """La guarda escala sola: si alguien agrega una tarjeta nueva, sigue cubierta.

    No enumera las 8 tarjetas de hoy — comprueba que el mecanismo que las protege
    (el ciclo por defecto) esta puesto mientras exista al menos una tarjeta agregada.
    """
    cfg = _dashboard(yaml_mod, TABLEROS_MULTICICLO[nombre])
    tarjetas = [c for c in cfg["charts"] if c.get("viz") == VIZ_AGREGADO_SIN_DIMENSION]
    if not tarjetas:
        pytest.skip(f"{nombre} no tiene tarjetas agregadas")
    ciclo = next(f for f in cfg["filtros_globales"] if f["columna"] == "id_ciclo")
    assert ciclo.get("valor_por_defecto"), (
        f"{nombre}: tiene {len(tarjetas)} tarjeta(s) agregada(s) "
        f"({[c['nombre'] for c in tarjetas]}) y ningun ciclo por defecto que las acote."
    )


# --------------------------------------------------------- clase 2: el traductor


def test_valor_por_defecto_se_traduce_a_default_data_mask(sync) -> None:
    """`valor_por_defecto` tiene que llegar a Superset como `defaultDataMask`."""
    cfg = {
        "filtros_globales": [
            {"columna": "id_ciclo", "etiqueta": "Ciclo", "datasets": ["ds"],
             "valor_por_defecto": "2024-2025"},
        ]
    }
    filtros = sync._filtros_nativos(cfg, {"ds": "uuid-1"})

    assert len(filtros) == 1
    mask = filtros[0].get("defaultDataMask")
    assert mask is not None, "no se emitio defaultDataMask"
    assert mask["extraFormData"]["filters"] == [
        {"col": "id_ciclo", "op": "IN", "val": ["2024-2025"]}
    ]
    assert mask["filterState"]["value"] == ["2024-2025"]


def test_un_valor_en_lista_tambien_funciona(sync) -> None:
    """Multi-select: aceptar una lista, no solo un escalar."""
    cfg = {
        "filtros_globales": [
            {"columna": "id_ciclo", "datasets": ["ds"],
             "valor_por_defecto": ["2023-2024", "2024-2025"]},
        ]
    }
    mask = sync._filtros_nativos(cfg, {"ds": "u"})[0]["defaultDataMask"]
    assert mask["filterState"]["value"] == ["2023-2024", "2024-2025"]
    assert mask["extraFormData"]["filters"][0]["val"] == ["2023-2024", "2024-2025"]


def test_sin_la_clave_el_filtro_queda_exactamente_como_antes(sync) -> None:
    """Compatibilidad hacia atras — `sync_semantic_layer.py` es compartido de C2.

    Los tableros de Manuel, Monserrat y Oscar no declaran `valor_por_defecto`: no deben
    ganar un `defaultDataMask` ni cambiar en nada por este cambio.
    """
    cfg = {"filtros_globales": [{"columna": "nivel", "datasets": ["ds"]}]}
    filtro = sync._filtros_nativos(cfg, {"ds": "u"})[0]
    assert "defaultDataMask" not in filtro, (
        "un filtro sin `valor_por_defecto` gano un defaultDataMask: el cambio dejo de ser "
        "aditivo y afecta a los tableros de otras personas."
    )
    assert set(filtro) == {
        "id", "name", "filterType", "type", "controlValues", "targets", "scope",
    }


def test_los_indices_de_los_filtros_no_cambian_al_fijar_un_defecto(sync) -> None:
    """El defecto no puede correr los IDs por posicion — romperia el drill-down.

    Los links de `link_db03`/`link_db04` apuntan a `NATIVE_FILTER-US203-{indice}`.
    """
    cfg = {
        "filtros_globales": [
            {"columna": "a", "datasets": ["ds"]},
            {"columna": "b", "datasets": ["ds"], "valor_por_defecto": "x"},
            {"columna": "c", "datasets": ["ds"]},
        ]
    }
    filtros = sync._filtros_nativos(cfg, {"ds": "u"})
    assert [f["id"] for f in filtros] == [
        "NATIVE_FILTER-US203-0",
        "NATIVE_FILTER-US203-1",
        "NATIVE_FILTER-US203-2",
    ]
