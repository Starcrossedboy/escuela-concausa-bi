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
| US-004 | in_review | 2026-08-03 | — | [[02_Requirements/Traceability_Matrix]] · [[13_Reports/PM_Dashboard_Spec]] (calendario con responsable visible) | 2026-08-12 |
| US-101 | done | 2026-08-02 | — | [[03_Architecture/Data_Model]] · [[_DevLog/2026-08-07-diana-alvarez-data-model-us101]] · PR #9 · PR #30 (columna indice_riesgo) | 2026-08-17 |
| US-102 | done | 2026-08-11 | — | [[_DevLog/2026-08-16-diana-alvarez-us102-fix-import-errors]] · PR #29 (DAGs de Airflow para las 8 fuentes) · PR #38 (fix de importación en dags) | 2026-08-17 |
| US-111 | done | 2026-08-12 | — | [[_DevLog/2026-08-16-deni-garrido-us111-bronze-silver-cierre]] · PR #37 (transformaciones Bronze → Silver con dbt) | 2026-08-17 |
| US-112 | in_progress | 2026-08-14 | — | PR #31 (US-112b parcial) · PR #39 (Silver → Gold, avance); vence en S3 | 2026-08-17 |
| US-113 | in_progress | 2026-08-15 | — | PR #32 (cubos de agregación DB-03/DB-04, avance); vence en S3 | 2026-08-17 |
| US-121b | done | 2026-08-13 | — | [[_DevLog/2026-08-14-luis-garcia-us121b-prueba-descarga]] · PR #31 (prueba de descarga real DS-04/DS-05) | 2026-08-17 |
| US-122b | in_review | 2026-08-14 | — | PR #31 (extractores de DS-04 y DS-05); falta DevLog/validación para `done` | 2026-08-17 |
| US-201 | done | 2026-08-07 | — | [[04_UX_Design/Screen_Specs]] · [[_DevLog/2026-08-07-manuel-serrania-us-201]] · PR #10 · PR #27/#36 (KPIs 15-18, JOIN a predicciones) | 2026-08-17 |
| US-202 | done | 2026-08-15 | — | [[_DevLog/2026-08-16-manuel-serrania-us202-superset]] · PR #39 (Superset: conexión, datasets y capa semántica) | 2026-08-17 |
| US-206 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-207 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-211a | in_review | 2026-08-15 | — | PR #32 · PR #39 (métricas y jerarquías de cubos DB-03/DB-04) · DevLog Marina; vence en S3 | 2026-08-17 |
| US-301 | done | 2026-08-09 | — | [[03_Architecture/ADRs/ADR-003-ml-estrategia-modelado]] · [[_DevLog/2026-08-09-andres-gonzalez-us301-estrategia-modelado]] · PR #12 | 2026-08-10 |
| US-302 | in_progress | 2026-08-16 | — | PR #33 (avance independiente ML/agente); vence en S4 | 2026-08-17 |
| US-303 | in_progress | 2026-08-16 | — | PR #33 (avance independiente ML/agente); vence en S4 | 2026-08-17 |
| US-304a | in_progress | 2026-08-16 | — | PR #33 (avance independiente ML/agente); vence en S5 | 2026-08-17 |
| US-304b | in_progress | 2026-08-16 | — | PR #33 (avance independiente ML/agente, Carlos); vence en S5 | 2026-08-17 |
| US-305 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-311 | done | 2026-08-08 | — | [[_DevLog/2026-08-13-hector-morales-entrenamiento-ml01]] · PR #28 (ML-01 entrenado, **MAE 0.0141 / RMSE 0.0177**, backtesting walk-forward + MLflow, TEST-005) · PR #8 (partición) · PR #21 (índice de riesgo) | 2026-08-17 |
| US-401 | done | 2026-08-03 | — | [[03_Architecture/API_Specification]] · `api/openapi.v1.json` · [[_DevLog/2026-08-11-christian-ruiz-us401-contrato-api]] · PR #19 (18 pruebas de contrato) | 2026-08-11 |
| US-405 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-501 | done | 2026-08-09 | — | [[08_CICD_DevOps/Cloud_Run_Deploy]] · [[_DevLog/2026-08-09-luis-tellez-us501-cloud-run-deploy]] · PR #13 (URL pública viva) | 2026-08-10 |
| US-502 | done | 2026-08-13 | — | [[_DevLog/2026-08-15-luis-tellez-us502-docker-compose-ml-services]] · PR #34 (MLflow/Superset/ChromaDB con hardening) · PR #35 (docker-compose del ecosistema) | 2026-08-17 |
| US-503 | done | 2026-08-14 | — | [[_DevLog/2026-08-15-luis-tellez-us503-ci-pipeline]] · PR #35 (pipeline CI completo con GitLeaks y pip-audit) | 2026-08-17 |
| US-504 | in_progress | 2026-08-16 | — | PR #34 (hardening de MLflow/Superset/ChromaDB, avance); vence en S4 | 2026-08-17 |
| US-505 | in_progress | 2026-08-16 | — | PR #34 (avance temprano de rollback/observabilidad); vence en S6 | 2026-08-17 |
| US-521a | done | 2026-08-12 | — | [[_DevLog/2026-08-12-alejandro-velazquez-mendoza]] · PR #25 (docker-compose + guía local API/Postgres) | 2026-08-17 |
| US-521b | in_progress | 2026-08-09 | — | [[_Meta/US-521b-guia-ambiente-local]] · [[_DevLog/2026-08-09-edgar-jimenez-setup]] · PR #14 · PR #29 (env DAGs); **verificar si el docker-compose de Airflow/ML ya queda cubierto por el compose del ecosistema (PR #35)** | 2026-08-17 |
| US-521c | in_review | 2026-08-12 | — | PR #23 (inventario de dependencias + ambiente local Superset/agente); falta DevLog para `done` | 2026-08-17 |

## Interpretación

**Reconciliación 2026-08-17 (cierre de S2 / arranque de S3).** Se incorporaron los PR #23–#39 que el
registro no reflejaba. Sprint 1 y Sprint 2 quedan esencialmente cerrados.

**`done` (PR + DevLog, Definition of Done):**
- **S1:** US-001/002/003 (Edgar) · US-101 (Diana, +columna `indice_riesgo` PR #30) · US-201 (Manuel) ·
  US-301 (Andrés) · US-401 (Christian) · US-501 (Luis Téllez) · US-121b (Luis E. García, PR #31) ·
  US-521a (Alejandro, PR #25).
- **S2:** US-102 (Diana · DAG maestro, PR #29/#38) · US-111 (Deni · Bronze→Silver, PR #37) ·
  US-502 (Luis Téllez · docker-compose del ecosistema, PR #34/#35) · US-503 (Luis Téllez · pipeline CI,
  PR #35).
- **S3/S4 adelantadas:** US-202 (Manuel · Superset, PR #39) · **US-311 (Héctor · ML-01 entrenado,
  MAE 0.0141 / RMSE 0.0177 + MLflow, PR #28)** — cierra el entregable que faltaba de ML.

**`in_review` (core entregado, falta DevLog/trazabilidad o mantenimiento):** US-004 (tablero PM,
continuo) · US-122b (extractores DS-04/05) · US-211a (cubos DB-03/04) · US-521c (ambiente Superset/agente).

**`in_progress`:** US-112/US-113 (Silver→Gold y cubos, Deni, S3) · US-302/303/304a/304b (Andrés/Carlos ·
avance independiente ML/agente, PR #33) · US-504/505 (Luis Téllez · hardening/observabilidad, PR #34) ·
US-521b (Edgar Jiménez · **verificar** si el compose del ecosistema ya lo cubre) · las cuatro de
**FARO Web** (US-206/207/305/405 · solo andamiaje, PR #7).

**⚠️ Hueco real (bloqueo de calendario):** **Emilio Galnares** no ha arrancado su ramo de **DS-06
(CONAGUA) y DS-08 (CONAPO)** — US-121a (prueba, S1), US-122a (extractores, S2) y US-123a (Great
Expectations, S3), todas suyas y encadenadas. Su par Luis E. García ya cerró el ramo simétrico
(DS-04/05). Es el único gap de S2 y arrastra 2 de las 8 fuentes hacia Gold. **Prioridad de destrabe.**

Para US de documentación/diseño, la "prueba" de Definition of Done la cubren la revisión del Tech Lead
responsable, `vault_lint` y TEST-002.
