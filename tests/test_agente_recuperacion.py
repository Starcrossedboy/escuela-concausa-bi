"""Pruebas del módulo de recuperación (RAG) (US-304b)."""

from unittest.mock import MagicMock

import pytest

from src.agente.recuperacion import ErrorRecuperacion, recuperar_contexto


def test_recuperar_contexto_exito():
    """Verifica el formateo con dependencias inyectadas, sin red ni descargas."""
    modelo = MagicMock()
    modelo.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2])
    cliente = MagicMock()
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Tabla dim_escuela (Dimensión)", "Tabla fact_escuela_ciclo (Hecho)"]]
    }
    cliente.get_collection.return_value = mock_collection

    res = recuperar_contexto(
        "háblame de escuelas y alumnos",
        modelo=modelo,
        cliente=cliente,
    )

    assert "Tablas relevantes" in res
    assert "dim_escuela" in res
    assert "fact_escuela_ciclo" in res
    mock_collection.query.assert_called_once()


def test_recuperar_contexto_coleccion_faltante():
    cliente = MagicMock()
    cliente.get_collection.side_effect = Exception("Collection not found")

    with pytest.raises(ErrorRecuperacion, match="ejecuta indexar_esquema.py"):
        recuperar_contexto("pregunta", modelo=MagicMock(), cliente=cliente)


def test_recuperar_contexto_vacio_falla_explicito():
    cliente = MagicMock()
    cliente.get_collection.return_value.query.return_value = {"documents": [[]]}
    modelo = MagicMock()
    modelo.encode.return_value = MagicMock(tolist=lambda: [0.1])

    with pytest.raises(ErrorRecuperacion, match="no devolvió contexto"):
        recuperar_contexto("pregunta", modelo=modelo, cliente=cliente)
