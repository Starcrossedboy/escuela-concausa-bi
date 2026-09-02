---
id: DOC-SLO
title: "Monitoring & SLOs"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
traces_up: ["PRD#6"]
tags: [ops, monitoring, slo]
---

# Monitoring & SLOs — FARO

> → [[vault/11_Operations/_index]]

## SLOs
| Servicio | SLI | Objetivo (SLO) |
|---|---|---|
| API | disponibilidad | 99.5% |
| API | latencia p95 | < X ms |

## Alertas

| Alerta | Condición | Canal | Runbook |
|---|---|---|---|
| Falla de task/DAG (Airflow) | Task o DAG termina en `failed` | Slack/Discord (`ALERT_WEBHOOK_URL`) | [[vault/11_Operations/Runbook_SLA_MLflow]] |
| SLA incumplido (Airflow) | Task tarda más de lo definido en `sla=` | Slack/Discord (`ALERT_WEBHOOK_URL`) | [[vault/11_Operations/Runbook_SLA_MLflow]] |
| Run de MLflow fallido | Último run de un experimento termina en `FAILED` | Slack/Discord (`ALERT_WEBHOOK_URL`) | [[vault/11_Operations/Runbook_SLA_MLflow]] |
| Métrica de modelo fuera de rango | Métrica clave fuera de `[MLFLOW_METRIC_MIN, MLFLOW_METRIC_MAX]` | Slack/Discord (`ALERT_WEBHOOK_URL`) | [[vault/11_Operations/Runbook_SLA_MLflow]] |
| Experimento MLflow sin runs / inexistente | Probable error de configuración | Slack/Discord (`ALERT_WEBHOOK_URL`) | [[vault/11_Operations/Runbook_SLA_MLflow]] |
| Falla del propio monitor | DAG `mlflow_monitor` falla por excepción no controlada | Slack/Discord (`ALERT_WEBHOOK_URL`) | [[vault/11_Operations/Runbook_SLA_MLflow]] |

## Dashboards
- Enlace al dashboard de observabilidad + [[vault/13_Reports/_index]].
