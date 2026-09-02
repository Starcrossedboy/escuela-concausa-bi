---
id: DOC-ROLLBACK
title: "Rollback Runbook"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
tags: [cicd, rollback, ops]
---

# Rollback Runbook — FARO

> Qué hacer cuando un deploy sale mal. → [[vault/08_CICD_DevOps/_index]] · [[vault/11_Operations/_index]]

## Criterios para revertir
- Error rate / latencia sobre umbral, caída de funcionalidad crítica, incidente de seguridad.

## Procedimiento
1. Declarar incidente (`INC-###` en [[vault/10_Risk_Governance/Incident_Log]]).
2. Revertir a la última versión estable (redeploy del tag anterior).
3. Verificar recuperación (smoke test + métricas).
4. Comunicar estado.
5. Post-mortem ([[vault/_Templates/Post_Mortem_template]]).

## Kill-switch
- Cómo deshabilitar la feature/flag afectada sin redeploy completo.
