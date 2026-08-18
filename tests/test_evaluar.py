"""Pruebas de la evaluación comparativa (US-312, TEST-007).

La prueba que sostiene AC-003.2 es `test_el_reporte_es_determinista`: si el documento del vault se
regenera igual, las cifras publicadas y las que produce el pipeline no pueden divergir.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.modelos.entrenar_ml01 import entrenar_y_evaluar as entrenar_ml01
from src.modelos.entrenar_ml02 import cargar_features_ml02
from src.modelos.entrenar_ml02 import entrenar_y_evaluar as entrenar_ml02
from src.modelos.evaluar import (
    cobertura_y_error,
    construir_reporte,
    curva_por_ventana,
    error_por_entidad,
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
