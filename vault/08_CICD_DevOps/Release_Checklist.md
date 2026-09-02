---
id: DOC-RELEASE
title: "Release Checklist"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [cicd, release]
---

# Release Checklist — FARO

> → [[vault/08_CICD_DevOps/_index]]

## Pre-release
- [ ] Matriz de trazabilidad sin celdas vacías para los REQ del release
- [ ] CI en verde (todos los gates)
- [ ] `/security-review` ejecutado sin hallazgos abiertos ≥ high ([[vault/07_Security/Security_Review_Checklist]])
- [ ] Pruebas físicas/manuales del happy path pasadas ([[vault/06_Quality_Testing/Physical_Manual/_index]])
- [ ] Bugs críticos/altos cerrados ([[vault/06_Quality_Testing/Bug_Register]])
- [ ] Changelog / notas de versión listas
- [ ] Plan de rollback confirmado ([[vault/08_CICD_DevOps/Rollback_Runbook]])
- [ ] Variables/secretos de prod verificados

## Release
- [ ] Tag de versión creado
- [ ] Deploy ejecutado por CI
- [ ] Smoke test post-deploy OK

## Post-release
- [ ] Monitoreo 24–48h
- [ ] DevLog de release
