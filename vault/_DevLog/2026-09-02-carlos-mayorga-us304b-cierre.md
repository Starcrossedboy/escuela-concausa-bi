---
id: DEVLOG-20260902-CM
author: Carlos Guillermo Mayorga Tapia
date: 2026-09-02
tags: [RAG, US-304b, chroma, docker]
---
# Cierre US-304b y Hallazgo de Dependencias

- **Objetivo:** Verificar la recuperación RAG dentro del contenedor de la API (US-304b).
- **Proceso:** 
  - Se levantaron los contenedores de `chromadb` y `api`.
  - El contenedor de la API no contiene las dependencias de Célula 3 (`chromadb`, `sentence-transformers`) por diseño (indicado en `requirements.txt`).
  - Para no modificar archivos fuera de nuestro alcance (Célula 5), se instaló `chromadb` y `sentence-transformers` en el `.venv` local y se probó apuntando al puerto `8001` expuesto por Docker.
- **Resultado:**
  - El script `src/agente/indexar_esquema.py` logró indexar 7 documentos del esquema Gold exitosamente.
  - La prueba con `src/agente/recuperacion.py` recuperó exitosamente el contexto esperado (tablas `dim_escuela`, `predicciones` y `dim_municipio`).
- **Siguientes Pasos (Hallazgo Operativo):** 
  - Si se planea que la API en Docker sirva las respuestas del Agente, la Célula 5 deberá modificar el `api.Dockerfile` para incorporar `requirements/celula-3.txt`.

# Cierre Total del Sprint

Adicionalmente, se resolvieron las dos correcciones pendientes marcadas en el plan de sprint:
1. **US-304b (Refactorización):** Se implementó *lazy loading* y *caching* para la instanciación de `SentenceTransformer` en `src/agente/recuperacion.py`. Se agregó manejo de errores con el módulo `logging` para evitar que las fallas de conexión a HuggingFace sean devoradas silenciosamente, resolviendo así el bloqueo potencial para el despliegue en Cloud Run. Las pruebas de pytest (`test_agente_recuperacion.py`) pasaron exitosamente.
2. **US-324 (Fichas de Modelo):** Se corrigió la ficha `ML03_Model_Card.md`, eliminando la leyenda de "pendiente de entrenamiento" y colocando el resultado real del *Silhouette Score* (0.1086) obtenido por la historia US-321.
