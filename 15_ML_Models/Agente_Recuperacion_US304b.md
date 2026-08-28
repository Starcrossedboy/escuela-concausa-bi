---
id: DOC-AGENTE-RAG-US304B
title: "Agente FARO — Recuperación de Contexto (RAG)"
owner: "Carlos Guillermo Mayorga Tapia"
status: approved
version: "1.1"
traces_up: ["US-304b", "REQ-006"]
traces_down: ["src/agente/recuperacion.py", "src/agente/indexar_esquema.py", "tests/test_agente_recuperacion.py", "tests/test_agente_indexacion.py"]
tags: [agente, rag, embeddings, chromadb, celula-3]
---

# Agente FARO — Recuperación de Contexto (RAG)

> → [[15_ML_Models/_index]]

## Objetivo

US-304b establece la capa de recuperación (RAG) para el agente conversacional. Su propósito es inyectar contexto estático sobre el esquema de la capa Gold para que el modelo de lenguaje (Text-to-SQL) conozca qué tablas y columnas existen antes de generar la consulta, mitigando alucinaciones.

## Diseño y Arquitectura

- **Motor de Vectores**: ChromaDB (ejecutándose en Docker en el puerto 8001).
- **Modelo de Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (ligero y eficiente para textos cortos).
- **Esquema de Documentos**: Se utiliza una definición estática de las tablas Gold (derivada de la semántica en `schemas.py`) en lugar de reflexionar la base de datos viva.

## Componentes

1. **Job de Indexación (`src/agente/indexar_esquema.py`)**:
   - Script independiente e idempotente.
   - Crea la colección `faro_gold_schema` con espacio de distancia `cosine`.
   - Genera embeddings para las descripciones estáticas y las guarda (upsert).
   - Usa IDs deterministas, devuelve el total indexado y falla explícitamente si Chroma no responde.

2. **Módulo de Recuperación (`src/agente/recuperacion.py`)**:
   - Expone la función `recuperar_contexto(pregunta: str) -> str`.
   - Conecta a ChromaDB, vectoriza la pregunta y recupera los fragmentos de tabla más relevantes (top-k).
   - Formatea el resultado para su inyección en `construir_prompt_sistema`.
   - Carga el modelo de forma diferida y permite inyectar cliente/modelo en pruebas sin red.
   - Devuelve errores tipados cuando falta la colección, ChromaDB o contexto recuperado.

## Pruebas

Cubierto en `tests/test_agente_recuperacion.py`:
- Manejo seguro si la colección de ChromaDB no ha sido inicializada.
- Validación de que los resultados devueltos por el motor se integren correctamente en un string legible.

`tests/test_agente_indexacion.py` cubre upsert con IDs deterministas, catálogo actualizado con
`driver_dominante` y fallo visible ante errores de ChromaDB.
