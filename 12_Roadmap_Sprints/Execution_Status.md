---
id: PLAN-EXEC-STATUS
title: "Estado de ejecución — FARO"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: true
traces_up: ["02_Requirements/User_Stories", "12_Roadmap_Sprints/PLAN_MAESTRO"]
traces_down: ["13_Reports/PM_Dashboard_Spec", "02_Requirements/Traceability_Matrix"]
last_reviewed: "2026-08-05"
tags: [roadmap, execution, status, dashboard]
---

# Estado de ejecución — FARO

> Registro canónico de los campos **operativos** de cada historia. El catálogo, responsable, célula,
> sprint y REQ viven únicamente en [[02_Requirements/User_Stories]]. El tablero une ambos documentos.
> → [[12_Roadmap_Sprints/_index]] · [[13_Reports/PM_Dashboard_Spec]]

## Reglas

- Toda `US-###` ausente de la tabla se interpreta como `planned`; así no se duplica el catálogo.
- Estados válidos: `planned` → `in_progress` → `in_review` → `blocked` → `done`.
- `blocked` exige `bloqueo_desde` y un `BLOCK-###` en [[10_Risk_Governance/Blocker_Register]].
- `done` exige evidencia de PR/commit, prueba, DevLog y trazabilidad conforme a
  [[05_Engineering/Definition_of_Done]].
- El porcentaje del tablero se deriva del estado; nunca se captura manualmente.
- El PO actualiza este registro al cierre de cada standup.

## Historias con estado distinto de `planned`

| US | Estado | Inicio | Bloqueo desde | Evidencia | Actualizado |
|---|---|---|---|---|---|
| US-001 | done | 2026-08-01 | — | [[_DevLog/2026-08-03-handoff-cierre-planeacion]] · PR #3/#5 | 2026-08-10 |
| US-002 | done | 2026-08-01 | — | [[01_Product/PRD_General_Materia]] · [[02_Requirements/Requirements_Detailed]] | 2026-08-10 |
| US-003 | done | 2026-08-02 | — | [[09_AI_Governance/Agent_Contexts/_index]] · PR #3/#5 | 2026-08-10 |
| US-004 | in_review | 2026-08-03 | — | [[02_Requirements/Traceability_Matrix]] | 2026-08-10 |
| US-101 | done | 2026-08-02 | — | [[03_Architecture/Data_Model]] · [[_DevLog/2026-08-07-diana-alvarez-data-model-us101]] · PR #9 | 2026-08-10 |
| US-201 | done | 2026-08-07 | — | [[04_UX_Design/Screen_Specs]] · [[_DevLog/2026-08-07-manuel-serrania-us-201]] · PR #10 | 2026-08-10 |
| US-206 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-207 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-305 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-311 | done | 2026-08-08 | — | [[06_Quality_Testing/Automated/Particion_Temporal_ML01]] · [[_DevLog/2026-08-08-hector-morales-fixture-particion-temporal]] · PR #8 | 2026-08-10 |
| US-401 | done | 2026-08-03 | — | [[03_Architecture/API_Specification]] · `api/openapi.v1.json` · [[_DevLog/2026-08-11-christian-ruiz-us401-contrato-api]] · PR #19 (18 pruebas de contrato) | 2026-08-11 |
| US-405 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-301 | done | 2026-08-09 | — | [[03_Architecture/ADRs/ADR-003-ml-estrategia-modelado]] · [[_DevLog/2026-08-09-andres-gonzalez-us301-estrategia-modelado]] · PR #12 | 2026-08-10 |
| US-501 | done | 2026-08-09 | — | [[08_CICD_DevOps/Cloud_Run_Deploy]] · [[_DevLog/2026-08-09-luis-tellez-us501-cloud-run-deploy]] · PR #13 (URL pública viva) | 2026-08-10 |
| US-521b | in_progress | 2026-08-09 | — | [[_Meta/US-521b-guia-ambiente-local]] · [[_DevLog/2026-08-09-edgar-jimenez-setup]] · PR #14 (docker-compose pendiente) | 2026-08-10 |

## Interpretación

**Sprint 1 cerrado (2026-08-10).** Las historias `done` cumplieron Definition of Done y quedaron
mergeadas a `main`:

- **US-001, US-002, US-003** (Edgar · gobernanza y planeación) — PR #2/#3/#5.
- **US-101** (Diana · `Data_Model`) — PR #9.
- **US-201** (Manuel · portafolio de 10 dashboards + catálogo de KPIs) — PR #10.
- **US-311** (Héctor · partición temporal ML con **TEST-003**) — PR #8.
- **US-301** (Andrés · estrategia de modelado: ADR-003, `ML_Strategy`, split temporal + tests) — PR #12.
- **US-501** (Luis · deploy Hello World a Cloud Run, **URL pública viva**) — PR #13.
- **US-401** (Christian · contrato OpenAPI v1 + stub FastAPI + 18 pruebas de contrato) — PR #19.

**En progreso (no `done`):** las cuatro US de **FARO Web** (US-206, US-207, US-305, US-405) tienen
solo el **andamiaje** merged (PR #7: ADR-002, `Frontend_Architecture`, esqueleto); su implementación
va en S4/S5. **US-521b** (Edgar Jiménez · guía de ambiente local, PR #14) queda `in_progress` porque
falta el `docker-compose`. **US-004** (matriz de trazabilidad) se mantiene `in_review` por ser un
artefacto de mantenimiento continuo. Para US de documentación/diseño, la "prueba" de Definition of Done
la cubren la revisión del Tech Lead responsable, `vault_lint` y TEST-002.
