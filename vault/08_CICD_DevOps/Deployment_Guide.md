---
id: DOC-DEPLOY
title: "Deployment Guide"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
tags: [cicd, deploy]
---

# Deployment Guide — FARO

> → [[vault/08_CICD_DevOps/_index]]

## Estrategia
- Deploy automático desde `main` tras gates en verde (ver [[vault/08_CICD_DevOps/CI_Quality_Gates]]).
- Solo el pipeline despliega a producción; nadie despliega a mano.

## Pasos (referencia)
```bash
# build → deploy vía CI
```

## Post-deploy
- Smoke test de endpoints/URL pública.
- Verificar métricas y logs ([[vault/11_Operations/Monitoring_SLOs]]).
- Si falla: [[vault/08_CICD_DevOps/Rollback_Runbook]].
