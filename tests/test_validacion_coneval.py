"""Pruebas offline de la suite Great Expectations de DS-07 CONEVAL."""

from __future__ import annotations

import pandas as pd

import great_expectations as gx
from src.ingesta.validacion_coneval import SUITE_NAME, construir_suite, validar


def _df_limpio() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "cve_mun": "09002",
                "periodo_medicion": 2020,
                "indice_rezago_social": -1.15,
                "indice_rezago_social_cobertura": "OK",
                "grado_rezago": "BAJO",
                "pobreza_pct": 24.2,
                "pobreza_pct_cobertura": "OK",
            },
            {
                "cve_mun": "15001",
                "periodo_medicion": 2020,
                "indice_rezago_social": None,
                "indice_rezago_social_cobertura": "SIN_DATO",
                "grado_rezago": "SIN_DATO",
                "pobreza_pct": None,
                "pobreza_pct_cobertura": "SIN_DATO",
            },
        ]
    )


def test_suite_ds07_declara_las_quince_expectativas() -> None:
    context = gx.get_context(mode="ephemeral")
    suite = construir_suite(context)

    assert suite.name == SUITE_NAME
    assert len(suite.expectations) == 15
    assert any(
        expectativa.expectation_type == "expect_compound_columns_to_be_unique"
        and expectativa.column_list == ["cve_mun", "periodo_medicion"]
        for expectativa in suite.expectations
    )


def test_datos_limpios_pasan_todas_las_expectativas() -> None:
    context = gx.get_context(mode="ephemeral")

    resultado = validar(_df_limpio(), context)

    assert resultado.success is True
    assert resultado.statistics["successful_expectations"] == 15


def test_detecta_brechas_de_contrato_y_cobertura() -> None:
    df = pd.DataFrame(
        [
            {
                "cve_mun": "09002",
                "periodo_medicion": 2020,
                "indice_rezago_social": None,
                "indice_rezago_social_cobertura": "OK",
                "grado_rezago": "DESCONOCIDO",
                "pobreza_pct": 120.0,
                "pobreza_pct_cobertura": "OK",
            },
            {
                "cve_mun": "09002",
                "periodo_medicion": 2020,
                "indice_rezago_social": 0.4,
                "indice_rezago_social_cobertura": "SIN_DATO",
                "grado_rezago": "ALTO",
                "pobreza_pct": 10.0,
                "pobreza_pct_cobertura": "SIN_DATO",
            },
            {
                "cve_mun": "ABC",
                "periodo_medicion": 2021,
                "indice_rezago_social": 0.2,
                "indice_rezago_social_cobertura": "INVALIDA",
                "grado_rezago": "MEDIO",
                "pobreza_pct": None,
                "pobreza_pct_cobertura": "INVALIDA",
            },
        ]
    )
    context = gx.get_context(mode="ephemeral")

    resultado = validar(df, context)

    assert resultado.success is False
    fallos = {
        (
            validacion.expectation_config.type,
            validacion.expectation_config.kwargs.get("column"),
        )
        for validacion in resultado.results
        if not validacion.success
    }
    assert ("expect_compound_columns_to_be_unique", None) in fallos
    assert ("expect_column_values_to_match_regex", "cve_mun") in fallos
    assert ("expect_column_values_to_be_between", "pobreza_pct") in fallos
    assert ("expect_column_values_to_be_in_set", "grado_rezago") in fallos
    assert ("expect_column_values_to_be_in_set", "indice_rezago_social_cobertura") in fallos
    assert ("expect_column_values_to_be_in_set", "pobreza_pct_cobertura") in fallos
    assert ("expect_column_values_to_not_be_null", "indice_rezago_social") in fallos
    assert ("expect_column_values_to_be_null", "indice_rezago_social") in fallos
    assert ("expect_column_values_to_be_null", "pobreza_pct") in fallos
