"""Pruebas de guardarrailes del agente conversacional (US-304a)."""

from __future__ import annotations

import pytest

from src.agente.guardrails import aplicar_limit, pregunta_en_alcance, preparar_sql_seguro, validar_sql_lectura


def test_pregunta_de_faro_esta_en_alcance() -> None:
    resultado = pregunta_en_alcance("Que escuelas tienen mayor riesgo por inseguridad?")
    assert resultado.permitido


def test_pregunta_fuera_de_dominio_se_rechaza() -> None:
    resultado = pregunta_en_alcance("Cual es la mejor receta de pasta?")
    assert not resultado.permitido
    assert resultado.razon == "Pregunta fuera del alcance de FARO."


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM gold.predicciones",
        "UPDATE gold.escuelas SET nombre = 'x'",
        "DROP TABLE gold.features_escuela",
        "SELECT * FROM gold.escuelas; DELETE FROM gold.escuelas",
    ],
)
def test_sql_de_escritura_o_multiple_se_rechaza(sql: str) -> None:
    assert not validar_sql_lectura(sql).permitido


def test_sql_select_se_permite() -> None:
    assert validar_sql_lectura("SELECT cct FROM gold.features_escuela").permitido


def test_limit_se_agrega_si_falta() -> None:
    assert aplicar_limit("SELECT cct FROM gold.features_escuela") == (
        "SELECT cct FROM gold.features_escuela LIMIT 1000;"
    )


def test_limit_se_reduce_si_excede_el_maximo() -> None:
    assert aplicar_limit("SELECT cct FROM gold.features_escuela LIMIT 5000") == (
        "SELECT cct FROM gold.features_escuela LIMIT 1000;"
    )


def test_preparar_sql_seguro_falla_con_verbo_prohibido() -> None:
    with pytest.raises(ValueError, match="verbo prohibido"):
        preparar_sql_seguro("WITH borrado AS (DELETE FROM gold.predicciones) SELECT 1")
