"""Job idempotente para indexar el esquema de Gold en ChromaDB (US-304b)."""

import os
import chromadb
from sentence_transformers import SentenceTransformer

# Definiciones estáticas basadas en la capa Gold (repositorio y schemas.py)
# Estas definiciones se vectorizan para que el agente recupere solo lo relevante.
ESQUEMA_GOLD = [
    {
        "id": "dim_escuela",
        "texto": "Tabla dim_escuela (Dimensión de Escuela). Contiene la información estática de cada Centro de Trabajo (CCT). Columnas: cct (llave primaria, 10 caracteres), nombre, nivel (ej. PRIMARIA, SECUNDARIA), cve_mun (clave municipio 5 caracteres), sostenimiento, latitud, longitud."
    },
    {
        "id": "dim_municipio",
        "texto": "Tabla dim_municipio (Dimensión de Municipio). Contiene datos a nivel municipal. Columnas: cve_mun (llave primaria, 5 caracteres), nombre_municipio, poblacion (total de habitantes), indice_rezago_social, pobreza_pct (porcentaje en pobreza)."
    },
    {
        "id": "fact_escuela_ciclo",
        "texto": "Tabla fact_escuela_ciclo (Hecho). Contiene la matrícula observada por escuela y ciclo escolar. Columnas: cct (llave foránea), id_ciclo (ej. 2024-2025), matricula_total. Es la tabla principal para conocer cuántos alumnos hay."
    },
    {
        "id": "predicciones",
        "texto": "Tabla predicciones (Salida de ML-01). Contiene el riesgo de pérdida de matrícula estimado. Columnas: cct, id_ciclo, indice_riesgo (flotante entre 0 y 1, donde 1 es máximo riesgo), tiene_prediccion (booleano), es_estimado_por_grupo (booleano). Sólo lectura."
    },
    {
        "id": "recomendaciones",
        "texto": "Tabla recomendaciones (Salida de ML-02). Contiene el driver dominante que explica el riesgo. Columnas: cct, id_ciclo, driver_dominante (puede ser D1 pobreza, D2 inseguridad, D3 infraestructura, D4 conectividad, D5 agua, D6 aire). Sólo lectura."
    },
    {
        "id": "features_escuela",
        "texto": "Tabla features_escuela (Contrato de ML). Contiene los drivers calculados para el modelo. Columnas: cct, id_ciclo, d1, d2, d3, d4, d5, d6, indice_completitud_drivers (porcentaje de drivers con datos)."
    }
]

def indexar_esquema(host: str = "localhost", port: int = 8001):
    """Genera embeddings del esquema y los guarda en ChromaDB."""
    try:
        # Usa variables de entorno si están presentes (ej. dentro de Docker)
        host = os.getenv("CHROMA_HOST", host)
        port = int(os.getenv("CHROMA_PORT", port))
        
        client = chromadb.HttpClient(host=host, port=port)
        
        # distance = cosine suele ser mejor para sentence transformers ligeros
        coleccion = client.get_or_create_collection(
            name="faro_gold_schema",
            metadata={"hnsw:space": "cosine"}
        )
        
        print("Cargando modelo de embeddings (all-MiniLM-L6-v2)...")
        modelo = SentenceTransformer("all-MiniLM-L6-v2")
        
        textos = [doc["texto"] for doc in ESQUEMA_GOLD]
        ids = [doc["id"] for doc in ESQUEMA_GOLD]
        
        print("Generando embeddings...")
        embeddings = modelo.encode(textos).tolist()
        
        print("Guardando en ChromaDB...")
        coleccion.upsert(
            ids=ids,
            documents=textos,
            embeddings=embeddings
        )
        print("Esquema indexado correctamente en ChromaDB (colección: faro_gold_schema).")
        
    except Exception as e:
        print(f"Error al indexar el esquema: {e}")

if __name__ == "__main__":
    indexar_esquema()
