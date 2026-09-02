---
id: DOC-ENVS
title: "Environments"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
tags: [cicd, environments]
---

# Environments — FARO

> → [[vault/08_CICD_DevOps/_index]]

| Entorno | Propósito | URL | Datos | Quién despliega |
|---|---|---|---|---|
| local | desarrollo | localhost | mock/emulador | dev |
| staging | validación | | datos de prueba | CI |
| producción | usuarios reales | | reales | CI (solo) |

## Reglas
- Secretos distintos por entorno ([[vault/07_Security/Secrets_Policy]]).
- Nada de datos reales en local/staging.
