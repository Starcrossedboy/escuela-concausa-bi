---
project: "FARO"
date: "2026-08-30"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
touches: ["US-303", "REQ-003"]
tags: [devlog, mlflow, registry, e2e, celula-3]
---

# DevLog — 2026-08-30 — US-303: E2E incremental de MLflow

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/15_ML_Models/Guia_Ejecucion_C3|Guía C3]]

## Objetivo

Validar el camino común de registro de ML-01, ML-02 y ML-03 contra un servidor MLflow real y
determinar qué falta para cerrar US-303.

## Ejecución y resultado

- Se inició MLflow `3.15.1` por HTTP en `127.0.0.1:5002`, con backend SQLite local y un worker.
- Se invocó `src.modelos.mlflow_utils.registrar_sklearn()` con los tres nombres canónicos.
- MLflow creó la versión `1` de `ML01_RegresionMatricula`, `ML02_DriverClasificador` y
  `ML03_ClusteringEscuelas`.
- Los artefactos y bases temporales quedaron bajo `_local/`, excluido del repositorio.
- No se usaron datos reales, credenciales ni servicios de producción.

## Bloqueos observados

- El build de `docker/mlflow.Dockerfile` alcanzó `pip install mlflow==3.15.1`, pero BuildKit no pudo
  descargar desde `files.pythonhosted.org` por `SSLV3_ALERT_HANDSHAKE_FAILURE`.
- El `.venv` existente está incompleto y mezcla paquetes de Python 3.12; no sirve como evidencia
  reproducible para la CLI final. Se evitó modificarlo.

## Estado

El registro conjunto real avanzó y confirma el helper compartido. US-303 sigue `in_review` hasta
repetir la verificación en el contenedor compartido y completar la exposición vía API con C4.
