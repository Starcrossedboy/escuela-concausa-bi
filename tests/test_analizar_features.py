"""Pruebas del diagnóstico de features y cobertura (US-322, US-325)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.modelos.analizar_features import (
    COLUMNA_TARGET,
    cobertura_por_driver,
    cobertura_por_entidad,
    columnas_excluidas_por_fuga,
    completitud_por_entidad,
    correlaciones_drivers,
    requerir_clave_municipio,
    resumen_eda,
    validar_features_para_analisis,
    variables_candidatas_ml03,
)
from src.modelos.contrato import DRIVERS


def test_fixture_cumple_contrato_para_diagnostico(features: pd.DataFrame) -> None:
    validar_features_para_analisis(features)


def test_detecta_cobertura_inconsistente(features: pd.DataFrame) -> None:
    inconsistente = features.copy()
    inconsistente.loc[0, "d5_agua"] = None
    inconsistente.loc[0, "d5_cobertura"] = "OK"

    with pytest.raises(ValueError, match="Cobertura inconsistente"):
        validar_features_para_analisis(inconsistente)


def test_detecta_llave_duplicada(features: pd.DataFrame) -> None:
    duplicado = pd.concat([features, features.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="filas duplicadas"):
        validar_features_para_analisis(duplicado)


def test_eda_reporta_nulos_y_correlacion(features: pd.DataFrame) -> None:
    reporte = resumen_eda(features)

    assert set(reporte["feature"]) == {*DRIVERS, "indice_completitud_drivers", COLUMNA_TARGET}
    assert pd.isna(reporte.loc[reporte["feature"] == COLUMNA_TARGET, "correlacion_target"].item())
    assert reporte["nulos"].sum() > 0


def test_correlaciones_excluyen_target(features: pd.DataFrame) -> None:
    matriz = correlaciones_drivers(features)

    assert set(matriz.columns) == {*DRIVERS, "indice_completitud_drivers"}
    assert COLUMNA_TARGET not in matriz.columns


def test_variables_ml03_excluyen_llaves_y_target() -> None:
    candidatas = variables_candidatas_ml03()

    assert set(candidatas).isdisjoint(columnas_excluidas_por_fuga())
    assert {"d5_dato_disponible", "d6_dato_disponible"} <= set(candidatas)


def test_cobertura_por_driver_cuadra_con_observaciones(features: pd.DataFrame) -> None:
    reporte = cobertura_por_driver(features)

    assert set(reporte["driver"]) == set(DRIVERS)
    assert (reporte["con_dato"] + reporte["sin_dato"] == len(features)).all()
    assert reporte["pct_sin_dato"].between(0, 1).all()


def test_cobertura_y_completitud_por_entidad(features: pd.DataFrame) -> None:
    cobertura = cobertura_por_entidad(features)
    completitud = completitud_por_entidad(features)

    assert set(cobertura["driver"]) == set(DRIVERS)
    assert set(cobertura["entidad"]) == set(completitud["entidad"])
    assert completitud["completitud_promedio"].between(0, 1).all()


def test_analisis_municipal_no_infiere_clave_desde_cct(features: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="requiere cve_mun"):
        requerir_clave_municipio(features)
