---
id: DOC-RUNBOOK-SLA-MLFLOW
title: "Runbook — Alertas de Airflow y MLflow"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
traces_up: ["PRD#6"]
tags: [ops, runbooks, monitoring, mlflow, airflow]
---

# Runbook — Alertas de Airflow y MLflow

> Procedimiento para atender alertas del mecanismo de monitoreo ligero
> (Airflow + MLflow), sin stack de observabilidad adicional.
> → [[11_Operations/_index]]
> → [[11_Operations/Monitoring_SLOs]]

## 1. Síntoma / disparador

Llega un mensaje al canal de Slack/Discord configurado en `ALERT_WEBHOOK_URL`
por alguna de estas causas:

- Una task o DAG de Airflow termina en estado `failed`.
- Una task incumple su SLA definido (`sla=...`).
- El último run de un experimento de MLflow termina en `FAILED`.
- Una métrica clave del último run está fuera de `[MLFLOW_METRIC_MIN, MLFLOW_METRIC_MAX]`.
- El experimento de MLflow no existe o no tiene runs todavía.
- El propio DAG `mlflow_monitor` falla por una excepción no controlada
  (ej. MLflow no responde).

## 2. Diagnóstico

1. Leer el mensaje completo de la alerta:
   - **Airflow:** incluye DAG, task, fecha de ejecución, mensaje de error
     y link directo a los logs (`log_url`).
   - **MLflow:** incluye `run_id`, nombre del experimento y la lista de
     problemas detectados.
2. Clasificar la severidad:
   - 🔴 **Rojo** = fallo confirmado (task rota, run en `FAILED`, métrica
     fuera de rango) → requiere acción.
   - 🟠 **Naranja** = advertencia/degradación (SLA incumplido, experimento
     sin runs) → revisar, no necesariamente acción inmediata.
3. Revisar los logs:
   - Airflow → usar el link incluido en la alerta.
   - MLflow → consultar el `run_id` directamente en la UI de MLflow.

## 3. Acción

- **Métrica de negocio/calidad del modelo fuera de rango**, en un run
  que ya está promovido o sirviendo en producción → aplica el runbook
  de rollback **US-525b** ([[08_CICD_DevOps/Rollback_Runbook]]) para
  revertir al modelo/versión anterior conocida como buena.
- **Fallo de infraestructura** (Airflow no pudo correr una task, MLflow
  no responde) → el rollback de US-525b **no aplica**; tratar como
  incidente de infraestructura (reintentar, revisar recursos, escalar
  si persiste).
- **Falso positivo** (ej. rango de métrica mal calibrado) → ajustar
  `MLFLOW_METRIC_MIN`/`MLFLOW_METRIC_MAX` en la configuración, no
  ignorar futuras alertas similares.

## 4. Verificación

- Confirmar que el DAG/task vuelve a correr en verde en su siguiente
  ejecución, o que el nuevo run de MLflow queda dentro de rango.
- Si se aplicó rollback (US-525b), verificar que el modelo revertido
  está sirviendo correctamente antes de cerrar el incidente.

## 5. Comunicación

- Publicar un mensaje de seguimiento en el mismo canal de Slack/Discord
  cuando la alerta quede resuelta, para que el equipo sepa que ya tiene
  dueño y no queda "flotando".
- Si el ajuste fue de configuración (rango de métrica, etc.), dejar
  constancia del cambio en el DevLog.

## Anexo — Configuración de referencia

**Webhook** (`ALERT_WEBHOOK_URL`, `ALERT_WEBHOOK_TYPE`): nunca se
hardcodea; vive en `.env` (no versionado) en local/Docker Compose, en
un `Secret` de Kubernetes, o en el mecanismo de variables de entorno
del proveedor de Airflow gestionado (MWAA, Composer, Astronomer).

**Variables de MLflow:** `MLFLOW_TRACKING_URI`, `MLFLOW_EXPERIMENT_NAME`,
`MLFLOW_METRIC_NAME`, `MLFLOW_METRIC_MIN`, `MLFLOW_METRIC_MAX`.

**Programación del chequeo:** vía DAG de Airflow (`dags/mlflow_monitor_dag.py`,
recomendado) cada 30 min, o alternativamente cron dentro de un contenedor
(ver detalle técnico en `scripts/mlflow_monitor.py`).

## Límites conocidos

- No guarda histórico de métricas de infraestructura (CPU, memoria,
  latencia) — requeriría un stack de series de tiempo, fuera de alcance.
- No dedupe alertas repetidas: un DAG que falla en cada reintento genera
  una alerta por intento (mitigado parcialmente con `retries`/`retry_delay`).
- No reemplaza la revisión manual del run en la UI de MLflow.
