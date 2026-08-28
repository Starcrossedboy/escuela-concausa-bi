"""Pruebas del set de evaluación del agente (US-323)."""

import json
from pathlib import Path

import pytest

from src.agente.guardrails import pregunta_en_alcance
from src.agente.servicio import procesar_consulta

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "preguntas_evaluacion.json"

@pytest.fixture
def set_evaluacion():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_set_evaluacion_tiene_20_casos_y_tres_categorias(set_evaluacion):
    assert len(set_evaluacion) == 20
    assert {item["categoria"] for item in set_evaluacion} == {
        "valida",
        "fuera_de_alcance",
        "insegura",
    }


def test_evaluacion_dominio_agente(set_evaluacion):
    """Verifica que el agente filtra correctamente las preguntas fuera de alcance."""
    for item in set_evaluacion:
        pregunta = item["pregunta"]
        categoria = item["categoria"]
        
        en_alcance = pregunta_en_alcance(pregunta)
        
        if categoria == "fuera_de_alcance":
            assert not en_alcance.permitido, f"Fallo en pregunta '{pregunta}': debió ser rechazada (fuera de alcance)."
        elif categoria == "valida":
            assert en_alcance.permitido, f"Fallo en pregunta '{pregunta}': debió ser aceptada (en alcance)."


def test_preguntas_validas_recorrer_flujo_completo(set_evaluacion):
    validas = [item for item in set_evaluacion if item["categoria"] == "valida"]
    ejecutadas: list[str] = []

    for item in validas:
        resultado = procesar_consulta(
            item["pregunta"],
            recuperar_contexto=lambda pregunta: "Tabla gold.features_escuela(cct)",
            generar_sql=lambda prompt, pregunta: "SELECT cct FROM gold.features_escuela",
            ejecutar_sql=lambda sql: ejecutadas.append(sql) or [{"cct": "09ABC0001X"}],
            redactar_respuesta=lambda pregunta, filas: "Respuesta basada en Gold.",
        )
        assert not resultado.fuera_de_alcance, item["pregunta"]
        assert resultado.sql_generado is not None

    assert len(ejecutadas) == len(validas)


def test_preguntas_fuera_de_alcance_no_invocan_dependencias(set_evaluacion):
    def no_debe_llamarse(*args):
        raise AssertionError("Una pregunta fuera de alcance no debe continuar")

    for item in set_evaluacion:
        if item["categoria"] != "fuera_de_alcance":
            continue
        resultado = procesar_consulta(
            item["pregunta"],
            recuperar_contexto=no_debe_llamarse,
            generar_sql=no_debe_llamarse,
            ejecutar_sql=no_debe_llamarse,
            redactar_respuesta=no_debe_llamarse,
        )
        assert resultado.fuera_de_alcance, item["pregunta"]
        assert resultado.sql_generado is None


def test_preguntas_inseguras_nunca_ejecutan_sql(set_evaluacion):
    ejecutadas: list[str] = []

    for item in set_evaluacion:
        if item["categoria"] != "insegura":
            continue
        resultado = procesar_consulta(
            item["pregunta"],
            recuperar_contexto=lambda pregunta: "Tabla gold.predicciones",
            generar_sql=lambda prompt, pregunta: "DELETE FROM gold.predicciones",
            ejecutar_sql=lambda sql: ejecutadas.append(sql) or [],
            redactar_respuesta=lambda pregunta, filas: "No debe responder.",
        )
        assert resultado.fuera_de_alcance, item["pregunta"]
        assert resultado.sql_generado is None

    assert not ejecutadas
