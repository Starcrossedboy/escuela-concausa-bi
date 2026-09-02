---
id: DEVLOG-2026-08-31-EDGAR-US524B
title: "DevLog — US-524b: Monitoreo de MLflow con alertas por webhook"
owner: "Edgar Ulises Jiménez López"
status: filed
version: "1.0"
traces_up: ["02_Requirements/User_Stories", "05_Engineering/../Sprint"]
traces_down: ["scripts/mlflow_monitor.py", "common_alerting/webhook.py", "dags/mlflow_monitor_dag.py", "ADR-009"]
last_reviewed: "2026-08-31"
tags: [devlog, devops, monitoreo, mlflow, us524b, celula-5]
---

# DevLog — 2026-08-31 — Edgar Ulises Jiménez López

**Historia:** `US-524b` · Monitoreo, logs y alertas de Airflow y jobs ML
**Requisito:** `REQ-005` · Deploy GCP
**Rama:** `feat/edgar-lopez-us524b-monitoring-alerts`
**Herramienta de IA usada:** FordLLM (asistente conversacional), en modo par de trabajo

## Qué se pidió

Implementar un mecanismo de monitoreo para los runs de MLflow (ML-01/02/03) que detecte runs fallidos
y métricas fuera de rango, y que notifique por webhook (Slack/Discord), agendado vía Airflow. Reutilizar
el módulo `common_alerting/` ya existente en el repo en vez de crear un cliente de notificación nuevo.

## Qué generó la IA

- Borrador inicial de `scripts/mlflow_monitor.py`, incluyendo la lógica de:
  - Consulta del último run de un experimento vía el cliente de MLflow.
  - Evaluación de dos condiciones de alerta: estado `FAILED` y métrica fuera de rango/faltante.
  - Integración con `common_alerting/webhook.py` para notificar.
- Ajuste de arquitectura (Paso C, propuesto por la IA y validado por mí): mover el `import mlflow`
  de nivel de módulo a dentro de `main()`, para que el DAG se pueda parsear en Airflow sin tener
  `mlflow` instalado en el *scheduler*.
- Borrador de `dags/mlflow_monitor_dag.py` agendando la tarea.
- 13 pruebas unitarias (`tests/test_webhook.py`, `tests/test_mlflow_monitor.py`), incluyendo una
  prueba de regresión específica para el import diferido.
- `ADR-009` documentando la decisión de arquitectura y las alternativas descartadas.
- Borrador de descripción de PR (`PR-us524b-monitoreo-mlflow-webhook.md`).

## Qué revisé y validé yo

- Corrí la suite completa del repo (`pytest tests/ -v`) para confirmar que los 13 tests nuevos no
  chocan con los ya existentes (`test_mlflow_utils.py`, `test_verificar_registry.py`) ni rompen nada:
  **656 passed, 5 skipped** (los 5 *skips* son preexistentes en `test_ml_strategy.py`, sin relación a
  este cambio).
- Confirmé manualmente el criterio de "import diferido" leyendo el archivo generado, verificando que
  `mlflow` solo aparece importado dentro de `main()` y no en el nivel superior del módulo.
- Corrí `python _Meta/scripts/vault_lint.py .` → **Vault limpio**.
- Detecté una primera colisión de numeración (`ADR-007` ya tomado por Héctor Morales) y una segunda
  colisión (`ADR-008` ya tomado por mi propia contenerización de `US-522b`, renombrada desde
  `ADR-007` en un PR distinto, ya mergeado a `main` en el commit `5eef05a`). Se resolvió usando
  `ADR-009` para este trabajo de monitoreo.
- Verifiqué el estado de mis ramas antes de continuar: `US-522b` ya está mergeada a `main`, por lo
  que actualicé mi rama de `US-524b` (`git merge origin/main`) antes de editar la Traceability
  Matrix, para no pisar la fila de `REQ-005` ya actualizada con la referencia a `ADR-008`.

## IDs tocados

- Historia: `US-524b`
- Requisito: `REQ-005`
- ADR: `ADR-009`
- Sin bugs nuevos registrados en esta sesión.

## Pendientes al cierre de este DevLog

- Actualizar Sección 9 del Sprint personal y fila de `REQ-005` en la Traceability Matrix (agregando
  `ADR-009` sin pisar la referencia existente a `ADR-008`).
- Abrir el PR en GitHub usando `PR-us524b-monitoreo-mlflow-webhook.md` como descripción.
- Pendiente de revisión por Luis Téllez Domínguez (Tech Lead, Célula 5).
