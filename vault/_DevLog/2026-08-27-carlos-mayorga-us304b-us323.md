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
  - Se crearon los documentos `vault/15_ML_Models/Agente_Recuperacion_US304b.md` y `vault/15_ML_Models/Agente_Evaluacion_US323.md`.
  - Se actualizó el índice general `vault/15_ML_Models/_index.md`.
  - Se actualizó la Matriz de Trazabilidad (`vault/02_Requirements/Traceability_Matrix.md`) reflejando las nuevas historias en el estado *En progreso*.

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

## 6. Corrección del PM · 2026-08-28

Ajustes aplicados por **Edgar Coronel (PM)** directamente sobre esta rama, para desbloquear el
ensayo E2E. Se documentan aquí porque cambian el contenido de US-304b, no sólo su empaquetado.

**Por qué no bastaba con esperar.** El PR estaba en conflicto, y mientras un PR está en conflicto
GitHub no puede construir el merge commit: **ningún workflow `pull_request` se dispara**. Los checks
nunca corrieron (`gh pr checks 108` → *no checks reported*), así que «ya no truena el CI» no estaba
verificado por nadie. Se comprobó en local, en un worktree aparte, antes de tocar nada.

1. **`vault/_DevLog/2026-08-27-handoff-us304b.md`: borrado.** No tenía frontmatter, así que reprobaba
   `vault_lint` y con él el check requerido `Calidad de codigo y vault`. Revisándolo no era un
   DevLog: era una nota de traspaso de otra herramienta («Handoff — Antigravity», *Current branch*,
   *Latest graph status*), en inglés, que se coló al commit. Nadie la referenciaba.

2. **Conflicto de `vault/15_ML_Models/_index.md`: resuelto.** `main` había reescrito las descripciones de
   `ML02_Clasificacion_Driver`, `Agente_Guardrails_US304a` y `Widget_Chat_US305`; esta rama traía
   las versiones anteriores más dos filas nuevas. Se conservaron las descripciones de `main` y se
   insertaron las dos filas nuevas en su lugar.

3. **`ESQUEMA_GOLD` corregido contra los modelos dbt**, no contra la memoria. El error de fondo
   estaba en `features_escuela`, que declaraba columnas `d1 … d6`. Esos nombres existen, pero en
   **otra tabla**: `fact_escuela_ciclo`. En `features_escuela` los drivers llevan nombre largo
   (`d1_pobreza … d6_aire`). Un índice RAG existe para darle al agente los nombres verdaderos; con
   los equivocados, todo el SQL que generara contra esa tabla fallaba.

   De paso se completaron las columnas que faltaban, cada una una pregunta que el agente no podía
   contestar: las seis de CEMABE en `dim_escuela` (`agua`, `drenaje`, `electricidad`, `sanitarios`,
   `internet`, `computadoras` — los drivers D3 y D4), `variacion_matricula` en
   `fact_escuela_ciclo`, y `cve_mun` / `nivel` en `predicciones`, que son las que hacen usable el
   grano dual de DEC-010.

   Se agregó además un documento `convencion_sin_dato`: la regla de que `SIN_DATO` **nunca** es
   cero es una regla del proyecto, y el agente tiene que conocerla para no inventar datos al
   agregar.

**Verificado tras los cambios:** `pytest tests/ -q` → 472 pasan, 5 omitidas · `vault_lint.py .` →
Vault limpio · tablero PM válido (TEST-002).

**Pendiente, de Carlos.** `SentenceTransformer(...)` se instancia **al importar el módulo** en
`recuperacion.py`. En CI no pasa nada porque la librería no está instalada, pero donde sí lo está
—el ambiente de C3 y el contenedor de la API— importar `recuperacion` descarga ~90 MB de
HuggingFace: una llamada de red en el arranque en frío de Cloud Run. Y si HuggingFace no responde,
`_modelo` queda en `None` **en silencio** y el agente contesta «no disponible» para siempre, sin
rastro en los logs. Debe pasar a carga perezosa y registrar la excepción en vez de tragársela. No
bloquea el ensayo; sí bloquea el despliegue.
