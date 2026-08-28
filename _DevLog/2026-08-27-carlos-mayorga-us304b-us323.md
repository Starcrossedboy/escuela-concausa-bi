---
id: DEVLOG-2026-08-27-US304B-US323
title: "Implementación Capa RAG (US-304b) y Set de Evaluación (US-323)"
author: "Carlos Guillermo Mayorga Tapia"
date: "2026-08-27"
tags: [agente, rag, embeddings, chromadb, evaluacion, qa, us-304b, us-323]
---

# Implementación Capa RAG (US-304b) y Set de Evaluación (US-323)

## 1. Contexto y Objetivos

- **US-304b**: Establecer la capa de recuperación (RAG) para inyectar contexto estático sobre el esquema de la capa Gold en el prompt del agente, usando ChromaDB.
- **US-323**: Construir un set de evaluación con 20 preguntas categorizadas (válidas, fuera de alcance, inseguras) y automatizar las pruebas para evaluar los guardarraíles.

## 2. Trabajo Realizado

- **`indexar_esquema.py` (US-304b)**: Se creó un script que define estáticamente las tablas Gold (`dim_escuela`, `dim_municipio`, `fact_escuela_ciclo`, `predicciones`, `recomendaciones`, `features_escuela`) de acuerdo con la semántica de la API, y usa `sentence-transformers/all-MiniLM-L6-v2` para indexarlas en ChromaDB (`faro_gold_schema`).
- **`recuperacion.py` (US-304b)**: Módulo expuesto para el agente. Recibe una pregunta, la vectoriza y extrae las descripciones relevantes del esquema Gold formateadas en texto plano.
- **`preguntas_evaluacion.json` (US-323)**: Archivo tipo *fixture* con 20 preguntas categorizadas.
- **Pruebas Automatizadas**:
  - `test_agente_evaluacion.py`: Valida que el filtro de dominio detenga las preguntas *fuera de alcance* y que el filtro SQL bloquee los comandos destructivos.
  - `test_agente_recuperacion.py`: Comprueba el comportamiento del RAG, incluyendo el manejo de fallas si ChromaDB no ha sido indexado o el modelo no está presente.
- **Documentación y Trazabilidad**:
  - Se crearon los documentos `15_ML_Models/Agente_Recuperacion_US304b.md` y `15_ML_Models/Agente_Evaluacion_US323.md`.
  - Se actualizó el índice general `15_ML_Models/_index.md`.
  - Se actualizó la Matriz de Trazabilidad (`02_Requirements/Traceability_Matrix.md`) reflejando las nuevas historias en el estado *En progreso*.

## 3. Decisiones Técnicas Relevantes

- **Definición de Documentos (RAG)**: En lugar de consultar directamente los metadatos de la base de datos viva (lo que podría generar problemas de seguridad o sincronización sin contexto de negocio), se extrajeron descripciones explícitas y enriquecidas derivadas de `schemas.py` y el modelo de datos.
- **Manejo de Errores RAG**: El sistema RAG se implementó de forma tolerante a fallos. Si no puede contactar a ChromaDB o falta el modelo, devuelve una advertencia en lugar de panicar, permitiendo que el LLM decida cómo proceder con menos contexto.

## 4. Siguientes Pasos

- Consolidar `construir_prompt_sistema()` en `prompt.py` para que, en conjunto con `recuperar_contexto()`, pase los filtros al modelo generativo real.
- Iniciar las pruebas de integración del LLM (Text-to-SQL) con estos guardarraíles y contexto ya ensamblados.

## 5. Correcciones (Feedback PR 108)

Se aplicaron ajustes sobre la marcha para asegurar la integración continua:
- Envoltura de importaciones pesadas (`chromadb`, `sentence_transformers`) en bloques `try...except` para evitar errores `ModuleNotFoundError` en GitHub Actions. Modificación correspondientes de los Mocks en las pruebas.
- Refinamiento de la definición de `predicciones` (se incluyeron las columnas reales y se indicó filtrar por `grano='escuela'`) y `recomendaciones` (inclusión explícita de `recomendacion` prescriptiva).
