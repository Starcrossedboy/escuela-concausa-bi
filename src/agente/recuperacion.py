"""Módulo de recuperación (RAG) para el agente FARO (US-304b)."""

from __future__ import annotations

import os
from typing import Any

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError:
    chromadb = None
    SentenceTransformer = None

NOMBRE_COLECCION = "faro_gold_schema"
NOMBRE_MODELO_EMBEDDINGS = "all-MiniLM-L6-v2"


class ErrorRecuperacion(RuntimeError):
    """La capa RAG no está disponible."""


class ContextoNoEncontrado(ErrorRecuperacion):
    """La capa RAG respondió, pero no encontró contexto para la pregunta."""


def _cargar_modelo() -> Any:
    if SentenceTransformer is None:
        raise ErrorRecuperacion("sentence-transformers no está instalado.")
    try:
        return SentenceTransformer(NOMBRE_MODELO_EMBEDDINGS)
    except Exception as exc:
        raise ErrorRecuperacion("No se pudo cargar el modelo de embeddings.") from exc


def recuperar_contexto(
    pregunta: str,
    top_k: int = 3,
    host: str = "localhost",
    port: int = 8001,
    *,
    modelo: Any | None = None,
    cliente: Any | None = None,
) -> str:
    """Recupera descripciones del esquema Gold relevantes para una pregunta."""
    if not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía.")
    if top_k < 1:
        raise ValueError("top_k debe ser mayor que cero.")

    modelo = modelo or _cargar_modelo()
    if cliente is None:
        if chromadb is None:
            raise ErrorRecuperacion("chromadb no está instalado.")
        try:
            cliente = chromadb.HttpClient(
                host=os.getenv("CHROMA_HOST", host),
                port=int(os.getenv("CHROMA_PORT", port)),
            )
        except Exception as exc:
            raise ErrorRecuperacion("No se pudo conectar con ChromaDB.") from exc

    try:
        coleccion = cliente.get_collection(name=NOMBRE_COLECCION)
    except Exception as exc:
        raise ErrorRecuperacion(
            f"La colección {NOMBRE_COLECCION!r} no existe; ejecuta indexar_esquema.py."
        ) from exc

    try:
        vector_pregunta = modelo.encode(pregunta).tolist()
        resultados = coleccion.query(
            query_embeddings=[vector_pregunta],
            n_results=top_k,
        )
    except Exception as exc:
        raise ErrorRecuperacion("Falló la consulta de contexto en ChromaDB.") from exc

    documentos = resultados.get("documents", [[]])[0]
    if not documentos:
        raise ContextoNoEncontrado("No se encontró contexto para la pregunta.")
    return "Tablas relevantes del esquema Gold:\n" + "".join(
        f"- {documento}\n" for documento in documentos
    )
