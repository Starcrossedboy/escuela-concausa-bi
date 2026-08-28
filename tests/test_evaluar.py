"""Pruebas de la evaluación comparativa (US-312, TEST-007).

La prueba que sostiene AC-003.2 es `test_el_reporte_es_determinista`: si el documento del vault se
regenera igual, las cifras publicadas y las que produce el pipeline no pueden divergir.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.modelos.contrato import DRIVERS
from src.modelos.entrenar_ml01 import entrenar_y_evaluar as entrenar_ml01
from src.modelos.entrenar_ml02 import cargar_features_ml02
from src.modelos.entrenar_ml02 import entrenar_y_evaluar as entrenar_ml02
from src.modelos.evaluar import (
    cobertura_y_error,
    construir_reporte,
    curva_por_ventana,
    drivers_en_el_modelo,
    error_por_entidad,
    exclusiones_por_ventana,
    tabla_comparativa,
)
from src.modelos.generar_fixture import SCOPE_ENTIDADES

VENTANAS = 3


@pytest.fixture(scope="module")
def features_ml02(features: pd.DataFrame) -> pd.DataFrame:
    return cargar_features_ml02()


@pytest.fixture(scope="module")
def res01(features: pd.DataFrame):
    return entrenar_ml01(features, n_ventanas=VENTANAS)


@pytest.fixture(scope="module")
def res02(features_ml02: pd.DataFrame):
    return entrenar_ml02(features_ml02, n_ventanas=VENTANAS)


# --------------------------------------------------------------------------- comparativa


def test_compara_los_dos_modelos_implementados(res01, res02) -> None:
    tabla = tabla_comparativa(res01, res02)
    assert set(tabla["modelo"]) == {"ML-01", "ML-02"}
    assert set(tabla["metrica"]) == {"MAE", "F1 macro"}


def test_ambos_modelos_superan_su_baseline(res01, res02) -> None:
    """Un modelo que no supera su baseline no aporta, sin importar su métrica."""
    tabla = tabla_comparativa(res01, res02)
    assert (tabla["mejora"] > 0).all()


def test_reporta_el_numero_de_ventanas(res01, res02) -> None:
    tabla = tabla_comparativa(res01, res02)
    assert (tabla["ventanas"] == VENTANAS).all()


# --------------------------------------------------------------------------- curva


def test_la_curva_cubre_todas_las_ventanas_de_ambos(res01, res02) -> None:
    curva = curva_por_ventana(res01, res02)
    assert len(curva) == VENTANAS * 2
    assert set(curva["modelo"]) == {"ML-01", "ML-02"}


def test_el_entrenamiento_crece_a_lo_largo_de_la_curva(res01, res02) -> None:
    """Walk-forward: cada ventana entrena con más pasado que la anterior."""
    curva = curva_por_ventana(res01, res02)
    for _, grupo in curva.groupby("modelo"):
        tamanos = grupo.sort_values("ventana")["n_entrena"].tolist()
        assert tamanos == sorted(tamanos)
        assert tamanos[0] < tamanos[-1]


# --------------------------------------------------------------------------- error por entidad


def test_desglosa_las_entidades_del_alcance(features: pd.DataFrame, res01) -> None:
    tabla = error_por_entidad(features, res01)
    assert set(tabla["entidad"]) <= set(SCOPE_ENTIDADES)
    assert (tabla["mae"] >= 0).all()
    assert tabla["mae"].is_monotonic_decreasing  # de peor a mejor


def test_la_desviacion_contra_el_global_es_coherente(features: pd.DataFrame, res01) -> None:
    """Alguna entidad debe estar por encima del global y alguna por debajo."""
    tabla = error_por_entidad(features, res01)
    assert tabla["desviacion_vs_global"].max() > 0
    assert tabla["desviacion_vs_global"].min() < 0


# --------------------------------------------------------------------------- cobertura


def test_relaciona_error_con_cobertura(features: pd.DataFrame, res01) -> None:
    tabla = cobertura_y_error(features, res01)
    assert list(tabla.columns) == ["tramo", "escuelas", "mae"]
    assert tabla["escuelas"].sum() == len(features[features["id_ciclo"] == max(features["id_ciclo"])])


# --------------------------------------------------------------------------- reporte


def test_el_reporte_es_determinista(features: pd.DataFrame, res01, res02) -> None:
    """AC-003.2 pide métricas reproducibles: dos generaciones deben dar el mismo documento."""
    primero = construir_reporte(features, res01, res02)
    segundo = construir_reporte(features, res01, res02)
    assert primero == segundo


def test_el_reporte_lleva_frontmatter_valido(features: pd.DataFrame, res01, res02) -> None:
    """Sin frontmatter con `id` y `owner`, vault_lint lo rechaza."""
    reporte = construir_reporte(features, res01, res02)
    assert reporte.startswith("---\n")
    assert "id: DOC-EVALUACION-MODELOS" in reporte
    assert "owner: \"Héctor Rafael Morales Marbán\"" in reporte


def test_el_reporte_advierte_que_los_datos_son_sinteticos(features, res01, res02) -> None:
    """Publicar métricas de un fixture sin decirlo sería engañoso."""
    reporte = construir_reporte(features, res01, res02)
    assert "datos sintéticos" in reporte
    assert "no son resultados de negocio" in reporte


def test_el_reporte_declara_ml03_pendiente(features, res01, res02) -> None:
    """AC-003.2 no está cerrado mientras falte el Silhouette de ML-03."""
    reporte = construir_reporte(features, res01, res02)
    assert "ML-03" in reporte
    assert "pendiente" in reporte
    assert "US-321" in reporte


def test_el_reporte_declara_el_target_de_ml02(features, res01, res02) -> None:
    """Si ML-02 usa el proxy, la cifra no significa lo mismo y hay que decirlo."""
    reporte = construir_reporte(features, res01, res02)
    assert res02.columna_target_usada in reporte


def test_el_reporte_alinea_umbrales_ml01_con_target_proporcional(features, res01, res02) -> None:
    reporte = construir_reporte(features, res01, res02)
    assert "ML-01 MAE < 0.03 (3 puntos porcentuales)" in reporte
    assert "RMSE < 0.05 (5 puntos porcentuales)" in reporte
    assert "MAE < 15 alumnos" not in reporte


def test_el_reporte_publicado_esta_sincronizado(features, res01, res02) -> None:
    """El documento versionado debe coincidir con lo que produce el generador **hoy**.

    Es la guarda que faltaba. Al alinear los umbrales (US-301) se cambió `evaluar.py` sin
    regenerar el reporte, y el vault quedó publicando la redacción anterior sin que nada avisara.
    Con esta prueba, cambiar el generador y olvidar `python -m src.modelos.evaluar` rompe el CI en
    vez de dejar cifras obsoletas en el vault — que es justo lo que AC-003.2 quiere evitar al pedir
    métricas reproducibles.
    """
    raiz = Path(__file__).resolve().parents[1]
    publicado = (raiz / "06_Quality_Testing/Automated/Evaluacion_Modelos.md").read_text(
        encoding="utf-8"
    )
    assert publicado == construir_reporte(features, res01, res02), (
        "El reporte publicado no coincide con el generador. "
        "Regenéralo con: python -m src.modelos.evaluar"
    )


# ------------------------------------------------- drivers en el modelo (petición del PM)


@pytest.fixture(scope="module")
def res01_sin_agua(features: pd.DataFrame):
    """El escenario de la demo: DS-06 sin descarga verificada, D5 entero en `SIN_DATO`."""
    sin_agua = features.copy()
    sin_agua["d5_agua"] = float("nan")
    return entrenar_ml01(sin_agua, n_ventanas=VENTANAS)


def test_el_reporte_se_genera_aunque_falte_un_driver(
    features: pd.DataFrame, res01_sin_agua, res02
) -> None:
    """Regresión: con un driver excluido, el reporte ni siquiera podía construirse.

    `error_por_entidad` y `cobertura_y_error` predecían con los seis drivers aunque el modelo se
    hubiera entrenado con cinco, y sklearn rechazaba la forma. Era justo el escenario que el PM
    necesita documentar para la demo.
    """
    sin_agua = features.copy()
    sin_agua["d5_agua"] = float("nan")

    reporte = construir_reporte(sin_agua, res01_sin_agua, res02)

    assert "d5_agua" in reporte
    assert "5 de 6" in reporte


def test_la_tabla_marca_el_driver_que_quedo_fuera(res01_sin_agua, res02) -> None:
    tabla = drivers_en_el_modelo(res01_sin_agua, res02)

    assert len(tabla) == len(DRIVERS)
    agua = tabla[tabla["driver"] == "d5_agua"].iloc[0]
    assert agua["ML-01"] == "**fuera**"
    pobreza = tabla[tabla["driver"] == "d1_pobreza"].iloc[0]
    assert pobreza["ML-01"] == "entró"


def test_sin_exclusiones_lo_dice_en_vez_de_callar(features: pd.DataFrame, res01, res02) -> None:
    """Una tabla vacía se lee como 'no se midió'; el texto tiene que afirmar la cobertura."""
    reporte = construir_reporte(features, res01, res02)

    assert "ningún driver quedó fuera" in reporte


def test_las_exclusiones_se_reportan_por_ventana(res01_sin_agua, res02) -> None:
    """La distinción de BUG-015: falta siempre (hueco de fuente) vs falta sólo en las viejas."""
    detalle = exclusiones_por_ventana(res01_sin_agua, res02)

    assert not detalle.empty
    assert set(detalle["modelo"]) <= {"ML-01", "ML-02"}
    assert detalle["sin_datos"].str.contains("d5_agua").any()
    assert detalle["ventana"].str.contains("entrena").all(), "la ventana debe ser identificable"


def test_excluidos_por_ventana_en_none_no_rompe(res01_sin_agua, res02) -> None:
    """ML-02 lo deja en `None` por omisión; el reporte no puede caerse por eso."""

    class ResultadoSinDetalle:
        drivers_usados = res02.drivers_usados
        drivers_excluidos = res02.drivers_excluidos
        excluidos_por_ventana = None

    detalle = exclusiones_por_ventana(res01_sin_agua, ResultadoSinDetalle())

    assert set(detalle["modelo"]) == {"ML-01"}
