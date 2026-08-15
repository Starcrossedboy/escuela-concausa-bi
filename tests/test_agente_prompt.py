"""Pruebas del prompt de sistema del agente (US-304a)."""

from __future__ import annotations

from src.agente.prompt import SYSTEM_PROMPT, construir_prompt_sistema


def test_prompt_declara_alcance_faro() -> None:
    assert "escuelas" in SYSTEM_PROMPT
    assert "drivers D1" in SYSTEM_PROMPT
    assert "fuera de alcance" in SYSTEM_PROMPT


def test_prompt_prohibe_sql_de_escritura() -> None:
    for verbo in ["DELETE", "UPDATE", "DROP", "INSERT", "ALTER", "TRUNCATE"]:
        assert verbo in SYSTEM_PROMPT


def test_prompt_exige_select_with_y_limit() -> None:
    assert "SELECT" in SYSTEM_PROMPT
    assert "WITH" in SYSTEM_PROMPT
    assert "LIMIT 1000" in SYSTEM_PROMPT


def test_construir_prompt_agrega_contexto_recuperado() -> None:
    prompt = construir_prompt_sistema("Tabla gold.features_escuela: cct, id_ciclo")
    assert prompt.startswith(SYSTEM_PROMPT)
    assert "Contexto recuperado de FARO" in prompt
    assert "gold.features_escuela" in prompt
