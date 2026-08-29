"""Pruebas de la suite de Great Expectations de DS-06 CONAGUA
(`src/ingesta/validacion_conagua.py`). No corren contra Bronze real -- solo
verifican que `construir_suite` arma las reglas esperadas, siguiendo el mismo
enfoque que `tests/test_extractor_sinaica.py` (probar la lógica propia, no la
librería de terceros)."""
from __future__ import annotations

import great_expectations as gx

from src.ingesta.validacion_conagua import SUITE_NAME, construir_suite


def _tipos_de_expectativa(suite: gx.ExpectationSuite) -> list[str]:
    return [exp.expectation_type for exp in suite.expectations]


def test_construye_la_suite_con_el_nombre_esperado(tmp_path) -> None:
    context = gx.get_context(mode="ephemeral")
    suite = construir_suite(context)

    assert suite.name == SUITE_NAME


def test_suite_incluye_las_siete_expectativas_esperadas() -> None:
    context = gx.get_context(mode="ephemeral")
    suite = construir_suite(context)

    tipos = _tipos_de_expectativa(suite)

    assert tipos.count("expect_column_values_to_not_be_null") == 4  # nombre_oficial, estado, cap_namo, id_presa
    assert "expect_column_values_to_be_unique" in tipos
    assert tipos.count("expect_column_values_to_be_between") == 2  # cap_namo, alt_cort
    assert len(tipos) == 7


def test_valida_id_presa_como_llave_unica_y_no_nula() -> None:
    context = gx.get_context(mode="ephemeral")
    suite = construir_suite(context)

    columnas_de_unicidad = [
        exp.column
        for exp in suite.expectations
        if exp.expectation_type == "expect_column_values_to_be_unique"
    ]

    assert columnas_de_unicidad == ["id_presa"]