---
project: "FARO"
date: "2026-08-20"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "2h"
touches: ["US-302", "US-303", "US-304a", "REQ-003", "REQ-006", "AC-003.4", "AC-003.6"]
tags: [devlog, celula-3, ml-02, shap, mlflow, agente, guardrails]
---

# DevLog — 2026-08-20 — ML-02, SHAP, Gold y guardarraíles

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se conectó ML-02 con el job batch de Gold: las clases se alinean uno-a-uno por `cct` e `id_ciclo`
  con las predicciones de ML-01 y se publican en `gold.recomendaciones` mediante UPSERT.
- Se agregó `explicar_driver()`, que entrega el contrato acordado con Célula 4: `cct`,
  `driver_dominante` y contribuciones SHAP canónicas `D1`…`D6`.
- Se agregó una prueba explícita de AC-003.6: dos escuelas con igual riesgo y distinto driver reciben
  recomendaciones diferentes.
- Se reforzó MLflow: preflight de compatibilidad obligatorio y confirmación de la versión creada en
  Registry, registrada como tag `registered_model_version`.
- Se endurecieron los guardarraíles del agente: `FROM` y `JOIN` solo pueden consultar `gold.*` o CTE
  definidos en la misma consulta.
- Se actualizaron los documentos canónicos de US-302, US-304a y la guía de ejecución de Célula 3.

## Validación

- Pruebas enfocadas de ML-02, Gold, MLflow y agente: **59 passed**.
- Suite completa del repositorio: **201 passed, 7 skipped**.
- Smoke test SHAP real sobre una escuela: seis contribuciones `D1`…`D6` generadas correctamente.
- Ruff sobre los archivos Python tocados: limpio.
- Diagnósticos de VS Code/Pylance: sin errores.

## Bloqueos y coordinación

- No se pudo validar el Registry contra Docker porque este checkout no tiene configuradas las
  variables locales de Compose (`API_PORT`, Postgres y MLflow). No se crearon ni solicitaron secretos.
- Célula 1 debe confirmar la etiqueta supervisada real; mientras tanto ML-02 usa
  `driver_dominante_proxy` y sus métricas no son todavía resultados de negocio.
- Christian Ruiz debe integrar `explicar_driver()` en `/predicciones/{cct}/explicacion`; no se tocó
  `src/api/**` por estar fuera del alcance de Andrés.
- Carlos Mayorga debe conectar los guardarraíles con la recuperación de US-304b.
- Héctor Morales debe revisar la actualización de `Publicacion_Gold.md`, artefacto de US-313 bajo su
  propiedad, realizada para eliminar la afirmación obsoleta de que ML-02 no existe.

## Próximo paso

Configurar el entorno local de Compose, registrar ML-02 con `--registrar-modelo` y adjuntar la versión
visible en MLflow como evidencia de AC-003.4.
