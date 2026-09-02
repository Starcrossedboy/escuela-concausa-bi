---
id: DOC-RUNBOOKS
title: "Runbooks"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
tags: [ops, runbooks]
---

# Runbooks — FARO

> Procedimientos paso a paso para operaciones comunes y de emergencia.
> → [[vault/11_Operations/_index]]

## Índice de runbooks
| Runbook | Cuándo | Enlace |
|---|---|---|
| Rollback de deploy | deploy fallido | [[vault/08_CICD_DevOps/Rollback_Runbook]] |
| Rotación de secretos | fuga sospechada | [[vault/07_Security/Secrets_Policy]] |
| Restaurar backup | pérdida de datos | <> |
| Escalar recursos | pico de carga | <> |
| Alertas Airflow/MLflow | falla de task, SLA incumplido, run de MLflow fallido o métrica fuera de rango | [[vault/11_Operations/Runbook_SLA_MLflow]] |

## Plantilla de runbook
1. Síntoma / disparador
2. Diagnóstico
3. Acción
4. Verificación
5. Comunicación
