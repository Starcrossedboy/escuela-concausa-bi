"""Pruebas del job idempotente de indexación RAG."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.agente.indexar_esquema import ESQUEMA_GOLD, ErrorIndexacion, indexar_esquema


def test_indexa_catalogo_con_ids_deterministas_mediante_upsert() -> None:
    cliente = MagicMock()
    modelo = MagicMock()
    modelo.encode.return_value = MagicMock(
        tolist=lambda: [[0.1, 0.2] for _ in ESQUEMA_GOLD]
    )

    total = indexar_esquema(cliente=cliente, modelo=modelo)

    assert total == len(ESQUEMA_GOLD)
    argumentos = cliente.get_or_create_collection.return_value.upsert.call_args.kwargs
    assert argumentos["ids"] == [documento["id"] for documento in ESQUEMA_GOLD]
    assert len(argumentos["documents"]) == total
    assert len(argumentos["embeddings"]) == total


def test_catalogo_incluye_driver_dominante_canonico() -> None:
    features = next(doc for doc in ESQUEMA_GOLD if doc["id"] == "features_escuela")

    assert "driver_dominante" in features["texto"]
    assert "argmax" in features["texto"]


def test_fallo_de_chroma_no_se_reporta_como_exito() -> None:
    cliente = MagicMock()
    cliente.get_or_create_collection.side_effect = OSError("sin conexión")

    with pytest.raises(ErrorIndexacion, match="No se pudo indexar"):
        indexar_esquema(cliente=cliente, modelo=MagicMock())