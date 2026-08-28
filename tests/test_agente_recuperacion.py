"""Pruebas del módulo de recuperación (RAG) (US-304b)."""

import pytest
from unittest.mock import patch, MagicMock
from src.agente.recuperacion import recuperar_contexto

def test_recuperar_contexto_sin_modelo():
    """Valida el manejo de error si el modelo local no puede cargarse."""
    with patch("src.agente.recuperacion._modelo", None):
        res = recuperar_contexto("prueba")
        assert "no disponible" in res

@patch("src.agente.recuperacion.chromadb.HttpClient")
@patch("src.agente.recuperacion._modelo")
def test_recuperar_contexto_exito(mock_modelo, mock_client):
    """Verifica el formateo exitoso de documentos recuperados."""
    # Mock del embedding
    mock_modelo.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2])
    
    # Mock de ChromaDB
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Tabla dim_escuela (Dimensión)", "Tabla fact_escuela_ciclo (Hecho)"]]
    }
    mock_client.return_value.get_collection.return_value = mock_collection
    
    res = recuperar_contexto("háblame de escuelas y alumnos")
    
    # Assertions
    assert "Tablas relevantes" in res
    assert "dim_escuela" in res
    assert "fact_escuela_ciclo" in res
    mock_collection.query.assert_called_once()

@patch("src.agente.recuperacion.chromadb.HttpClient")
@patch("src.agente.recuperacion._modelo")
def test_recuperar_contexto_coleccion_faltante(mock_modelo, mock_client):
    """Verifica que atrape el error si la colección no ha sido indexada."""
    mock_client.return_value.get_collection.side_effect = Exception("Collection not found")
    
    res = recuperar_contexto("pregunta")
    assert "ADVERTENCIA" in res
    assert "no existe" in res
