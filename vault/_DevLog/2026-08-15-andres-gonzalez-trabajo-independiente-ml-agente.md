---
project: "FARO"
date: "2026-08-15"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "avance de trabajo independiente: US-302, US-303 y US-304a"
touches: ["US-302", "US-303", "US-304a", "REQ-003", "REQ-006", "DOC-ML02-CLASIFICACION-DRIVER", "DOC-AGENTE-GUARDRAILS-US304A", "DOC-C3-GUIA-EJECUCION", "DOC-C3-PR-DRAFT-TRABAJO-INDEPENDIENTE"]
tags: [devlog, celula-3, ml, agente, guardrails, mlflow]
---

# DevLog — 2026-08-15 — trabajo independiente ML y agente

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/15_ML_Models/_index]]

## Qué se hizo
- Se creó `src/agente/guardrails.py` con guardarraíles para US-304a: validación de alcance FARO,
  rechazo de SQL de escritura/DDL, bloqueo de sentencias múltiples y normalización a `LIMIT 1000`.
- Se agregó `tests/test_agente_guardrails.py` para cubrir preguntas dentro/fuera de dominio y SQL
  seguro/inseguro.
- Se creó `src/modelos/entrenar_ml02.py` como scaffold de ML-02: backtesting temporal, target proxy
  `driver_dominante_proxy`, métricas F1 macro / accuracy / precision macro, recomendaciones por driver
  y función SHAP opcional.
- Se agregó `tests/test_entrenar_ml02.py` para validar target proxy, no fuga temporal, métricas acotadas
  y salida compatible con la API.
- Se creó `src/modelos/mlflow_utils.py` con nombres canónicos de modelos y helper común de registro
  MLflow con import diferido.
- Se agregó `tests/test_mlflow_utils.py` para fijar los nombres canónicos de US-303.
- Se agregó `src/agente/prompt.py` con `SYSTEM_PROMPT` y `construir_prompt_sistema()` para US-304a.
- Se agregó `tests/test_agente_prompt.py` para cubrir reglas obligatorias del prompt.
- Se conectó `src/modelos/entrenar_ml02.py` con el helper MLflow mediante `registrar_en_mlflow()` y
  opciones CLI `--tracking-uri`, `--sin-mlflow` y `--registrar-modelo`.
- Se agregó `vault/15_ML_Models/Preguntas_Coordinacion_C3.md` con preguntas puntuales para C1, C4, C5,
  Estefany, Carlos y PM.
- Se agregó `vault/15_ML_Models/Guia_Ejecucion_C3.md` con comandos mínimos para instalar dependencias,
  correr pruebas enfocadas, ejecutar ML-02 y validar el vault.
- Se agregó `vault/15_ML_Models/PR_Draft_Trabajo_Independiente_C3.md` con borrador de PR listo para pegar
  en GitHub, incluyendo alcance parcial, pruebas y bloqueantes.
- Se sincronizó `vault/15_ML_Models/ML_Strategy.md` con el contrato vigente de `gold.features_escuela`
  (`id_ciclo`, `target_variacion_matricula`, `d1_pobreza`…`d6_aire`, `*_cobertura`).
- Se agregaron los documentos `vault/15_ML_Models/ML02_Clasificacion_Driver.md` y
  `vault/15_ML_Models/Agente_Guardrails_US304a.md`, registrados en `vault/15_ML_Models/_index.md`.

## Sesión de IA
- **Agente / modelo:** GitHub Copilot.
- **Archivos creados/modificados:**
  - `src/agente/__init__.py`
  - `src/agente/guardrails.py`
  - `src/agente/prompt.py`
  - `src/modelos/entrenar_ml02.py`
  - `src/modelos/mlflow_utils.py`
  - `tests/test_agente_guardrails.py`
  - `tests/test_agente_prompt.py`
  - `tests/test_entrenar_ml02.py`
  - `tests/test_mlflow_utils.py`
  - `vault/15_ML_Models/ML_Strategy.md`
  - `vault/15_ML_Models/_index.md`
  - `vault/15_ML_Models/ML02_Clasificacion_Driver.md`
  - `vault/15_ML_Models/Agente_Guardrails_US304a.md`
  - `vault/15_ML_Models/Preguntas_Coordinacion_C3.md`
  - `vault/15_ML_Models/Guia_Ejecucion_C3.md`
  - `vault/15_ML_Models/PR_Draft_Trabajo_Independiente_C3.md`
  - `vault/_DevLog/2026-08-15-andres-gonzalez-trabajo-independiente-ml-agente.md`
  - `vault/_DevLog/_index.md`
- **Decisiones autónomas del agente:** avanzar primero piezas que no dependen de Gold real, MLflow
  desplegado, endpoints de Célula 4 ni RAG de Carlos; usar `driver_dominante_proxy` como fallback
  explícito mientras Célula 1 publica la etiqueta real.
- **Correcciones manuales:** pendientes de revisión humana línea por línea antes del PR.
- **Prompt inicial:** "avanza con todo lo que pueda hacer en este momento".

## Seguridad / calidad
- [x] Sin secretos hardcodeados.
- [x] Tests agregados/actualizados para guardarraíles, ML-02 y contrato MLflow.
- [x] DevLog enlaza a los IDs afectados.
- [x] `python -m compileall -q src/agente src/modelos tests/test_agente_guardrails.py tests/test_entrenar_ml02.py tests/test_mlflow_utils.py` pasó.
- [x] `py -3.12 -m compileall -q src/agente src/modelos tests/test_agente_prompt.py tests/test_agente_guardrails.py tests/test_entrenar_ml02.py tests/test_mlflow_utils.py` pasó.
- [x] Smoke test del prompt con `py -3.12` pasó (`prompt_limit=True`).
- [x] `python vault/_Meta/scripts/vault_lint.py .` pasó con `✅ Vault limpio`.
- [x] Se instalaron dependencias mínimas en `.venv` local: `pytest`, `pandas`, `numpy`, `scikit-learn`, `scipy`, `pydantic`.
- [x] `.\.venv\Scripts\python.exe -m pytest tests/test_agente_guardrails.py tests/test_agente_prompt.py tests/test_entrenar_ml02.py tests/test_mlflow_utils.py -q --tb=short` pasó: **25 passed in 7.71s**.
- [x] `.\.venv\Scripts\python.exe -m src.modelos.entrenar_ml02 --sin-mlflow` pasó contra fixture sintético: F1 macro `0.7945 ± 0.0241`, accuracy `0.8083`.
- [ ] El ambiente sigue en Python 3.12.10; el proyecto pide Python 3.11, así que conviene instalar/usar 3.11 antes del PR final si el equipo lo mantiene como requisito estricto.

## Bloqueantes
- Para cerrar US-302 con métrica de negocio falta que Célula 1 publique la etiqueta real
  `driver_dominante` en Gold o confirme su derivación canónica.
- Para cerrar US-303 faltan ML-03, el registro final de los tres modelos en MLflow y coordinación con
  Célula 4 para endpoints de inferencia.
- Para cerrar US-304a falta integrar estos guardarraíles en el servicio del agente cuando exista la capa
  RAG de US-304b.

## Próximos pasos
- Confirmar si el equipo acepta validar con `.venv` Python 3.12.10 o si exige recrearlo con Python 3.11.
- Confirmar con Diana / PM el contrato final de `driver_dominante`.
