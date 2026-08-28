"""Módulo de recuperación (RAG) para el agente FARO (US-304b)."""

import os
import chromadb
from sentence_transformers import SentenceTransformer

# Inicializar modelo de forma global para no recargarlo en cada consulta
try:
    _modelo = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _modelo = None

def recuperar_contexto(pregunta: str, top_k: int = 3, host: str = "localhost", port: int = 8001) -> str:
    """
    Vectoriza la pregunta, busca en ChromaDB los fragmentos del esquema más relevantes
    y los devuelve formateados en texto claro.
    
    Args:
        pregunta: La pregunta en lenguaje natural del usuario.
        top_k: Número de tablas/documentos a recuperar.
        host: Host de ChromaDB.
        port: Puerto de ChromaDB.
        
    Returns:
        Un string con las descripciones de las tablas relevantes, o un aviso si falla.
    """
    if not _modelo:
        return "ADVERTENCIA: Modelo de embeddings (sentence-transformers) no disponible."
        
    try:
        host = os.getenv("CHROMA_HOST", host)
        port = int(os.getenv("CHROMA_PORT", port))
        
        client = chromadb.HttpClient(host=host, port=port)
        
        try:
            coleccion = client.get_collection(name="faro_gold_schema")
        except Exception:
            # Colección no existe aún
            return "ADVERTENCIA: La colección 'faro_gold_schema' no existe. ¿Ejecutaste indexar_esquema.py?"
        
        vector_pregunta = _modelo.encode(pregunta).tolist()
        
        resultados = coleccion.query(
            query_embeddings=[vector_pregunta],
            n_results=top_k
        )
        
        documentos = resultados.get("documents", [[]])[0]
        if not documentos:
            return ""
            
        contexto = "Tablas relevantes del esquema Gold:\n"
        for doc in documentos:
            contexto += f"- {doc}\n"
            
        return contexto
        
    except Exception as e:
        return f"ADVERTENCIA: No se pudo recuperar el contexto desde ChromaDB ({str(e)})."
