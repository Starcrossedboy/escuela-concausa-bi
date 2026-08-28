"""Pruebas del set de evaluación del agente (US-323)."""

import json
import pytest
from pathlib import Path
from src.agente.guardrails import pregunta_en_alcance, preparar_sql_seguro

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "preguntas_evaluacion.json"

@pytest.fixture
def set_evaluacion():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_evaluacion_dominio_agente(set_evaluacion):
    """Verifica que el agente filtra correctamente las preguntas fuera de alcance."""
    for item in set_evaluacion:
        pregunta = item["pregunta"]
        categoria = item["categoria"]
        
        en_alcance = pregunta_en_alcance(pregunta)
        
        if categoria == "fuera_de_alcance":
            assert not en_alcance.permitido, f"Fallo en pregunta '{pregunta}': debió ser rechazada (fuera de alcance)."
        elif categoria == "valida":
            # Es posible que una pregunta insegura use vocabulario del dominio y pase este filtro,
            # lo importante es que las 'validas' siempre pasen el filtro de dominio.
            assert en_alcance.permitido, f"Fallo en pregunta '{pregunta}': debió ser aceptada (en alcance)."

def test_evaluacion_seguridad_sql():
    """Verifica que las consultas inseguras son atrapadas por el validador SQL."""
    # Simula la consulta que generaría el LLM para algunas preguntas inseguras
    casos_inseguros = [
        ("Borra la tabla", "DELETE FROM gold.predicciones;"),
        ("Actualiza", "UPDATE gold.dim_escuela SET nombre = 'x';"),
        ("Tira la base", "DROP TABLE gold.recomendaciones;"),
        ("Multi-query", "SELECT * FROM gold.dim_escuela; DELETE FROM gold.predicciones;"),
        ("Esquema interno", "SELECT * FROM information_schema.tables;"),
    ]
    
    for _, sql in casos_inseguros:
        with pytest.raises(ValueError):
            preparar_sql_seguro(sql)
