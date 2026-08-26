---
id: PLAN-EXEC-STATUS
title: "Estado de ejecución — FARO"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: true
traces_up: ["02_Requirements/User_Stories", "12_Roadmap_Sprints/PLAN_MAESTRO"]
traces_down: ["13_Reports/PM_Dashboard_Spec", "02_Requirements/Traceability_Matrix"]
last_reviewed: "2026-08-25"
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
| US-103 | done | 2026-08-15 | — | [[_DevLog/2026-08-19-diana-alvarez-us103-gold-estrella]] · PR #48 (esquema estrella Gold: dim_escuela, dim_municipio, fact_escuela_ciclo; 170 tests) | 2026-08-19 |
| US-104 | done | 2026-08-15 | — | [[_DevLog/2026-08-19-diana-alvarez-us104-features-escuela]] · PR #48 (gold.features_escuela con drivers D1-D4 reales); **target definido por DEC-007** (híbrido: variación `municipio × nivel` con serie SNIEE + features escuela con 911) — resuelve RISK-007 | 2026-08-19 |
| US-105 | done | 2026-08-18 | — | [[_DevLog/2026-08-19-diana-alvarez-us105-idw-calidad-aire]] · PR #52 (interpolación IDW de D6 calidad del aire + cobertura parcial e índice de confianza) | 2026-08-19 |
| US-106 | in_progress | 2026-08-23 | — | [[_DevLog/2026-08-23-diana-alvarez-us106-linaje-freeze]] · PR #77 ([[03_Architecture/Data_Lineage_US106]]: linaje nodo por nodo de fuente → dashboard). **El freeze no está declarado**: el documento sigue en `status: draft` y su checklist tiene 3 de 6 ítems abiertos (cubos de DEC-009 en US-113, RISK-008, y el propio cambio a `approved`). Diana la declara al 80% | 2026-08-25 |
| US-111 | done | 2026-08-12 | — | [[_DevLog/2026-08-16-deni-garrido-us111-bronze-silver-cierre]] · PR #37 (transformaciones Bronze → Silver con dbt) · PR #67 (alineación del `ciclo` canónico) · PR #82 (**BUG-009**: 11 vars de dbt con default permanente, DEC-011) | 2026-08-25 |
| US-112 | done | 2026-08-14 | — | [[_DevLog/2026-08-22-deni-garrido-us112-silver-gold]] · PR #72 (estrella Gold materializada + tests nativos unique/not_null/relationships/accepted_values) · PR #67 (ciclo canónico en Silver). El DevLog condicionaba el cierre a que PR #72 dejara de estar abierto; se mergeó el 22-ago | 2026-08-25 |
| US-113 | in_progress | 2026-08-15 | — | PR #32 (cubos de agregación DB-03/DB-04, avance) · PR #81 **abierto en borrador** (8 cubos Gold + 30 tests de contrato; Deni la declara al 92%, trabada por `cubo_pipeline`/DB-10 sin relación dbt de metadata de ingesta). Grano nuevo ratificado en **DEC-009**. Es el ítem que falta para el freeze de US-106 | 2026-08-25 |
| US-121b | done | 2026-08-13 | — | [[_DevLog/2026-08-14-luis-garcia-us121b-prueba-descarga]] · PR #31 (prueba de descarga real DS-04/DS-05) | 2026-08-17 |
| US-122b | done | 2026-08-14 | — | [[_DevLog/2026-08-18-luis-garcia-us122b-extractor-sinaica]] · PR #31 · PR #47 (extractor real de DS-05 SINAICA probado contra la API en vivo) | 2026-08-19 |
| US-123b | in_progress | 2026-08-18 | — | [[_DevLog/2026-08-21-luis-garcia-us123b-great-expectations-ds05]] · PR #47 · PR #63 (suite real de Great Expectations para DS-05 Bronze). **Mitad DS-05 lista, mitad DS-04 pendiente** en PR #85 abierto — Luis la declara al 50% | 2026-08-25 |
| US-201 | done | 2026-08-07 | — | [[04_UX_Design/Screen_Specs]] · [[_DevLog/2026-08-07-manuel-serrania-us-201]] · PR #10 · PR #27/#36 (KPIs 15-18, JOIN a predicciones) · PR #78 (alta de KPI-19/KPI-20 en el catálogo canónico) | 2026-08-25 |
| US-202 | done | 2026-08-15 | — | [[_DevLog/2026-08-16-manuel-serrania-us202-superset]] · PR #39 (Superset: conexión, datasets y capa semántica) | 2026-08-17 |
| US-203 | done | 2026-08-21 | — | [[_DevLog/2026-08-21-manuel-serrania-us203-tableros-db01-db02]] · [[_DevLog/2026-08-22-manuel-serrania-us203-filtros-nombres-reales]] · PR #71 (DB-01 Ejecutivo y DB-02 Mapa de riesgo, filtros AC-002.2 completos y nombres INEGI reales vía `gold.geo_municipio`) · `test_semantic_db01_db02` 47 casos ✅ · E2E Playwright 16/16 charts con datos | 2026-08-25 |
| US-206 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-207 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-211a | done | 2026-08-15 | — | [[_DevLog/2026-08-21-marina-garcia-cierre-us211a]] · PR #32 · PR #39 (métricas y jerarquías de cubos DB-03/DB-04, 28 casos `test_semantic_db03_db04`); grano de DB-04 registrado en **DEC-008** | 2026-08-21 |
| US-211b | done | 2026-08-22 | — | [[_DevLog/2026-08-22-monserrat-miranda-us211b-cubos-db05-db08]] · [[_DevLog/2026-08-22-monserrat-miranda-us211b-fix-revision-manuel]] · PR #73 (contrato semántico de DB-05/DB-08 en formato largo, 29 casos `test_semantic_db05_db08`) · PR #78 (alta de KPI-19/KPI-20, cierra §8.3); revisado y aprobado por Manuel Serranía; grano registrado en **DEC-009** | 2026-08-25 |
| US-301 | done | 2026-08-09 | — | [[03_Architecture/ADRs/ADR-003-ml-estrategia-modelado]] · [[_DevLog/2026-08-09-andres-gonzalez-us301-estrategia-modelado]] · PR #12 | 2026-08-10 |
| US-302 | in_review | 2026-08-16 | — | PR #33 (avance independiente ML/agente) · PR #58 (ML-02 clasificación de driver dominante con SHAP, integrado a Gold). `in_review` y no `done`: [[15_ML_Models/ML02_Clasificacion_Driver]] sigue en `status: in_review` | 2026-08-25 |
| US-303 | in_progress | 2026-08-16 | — | PR #33 (avance independiente ML/agente); vence en S4 | 2026-08-17 |
| US-304a | in_progress | 2026-08-16 | — | PR #33 (avance independiente ML/agente); vence en S5 | 2026-08-17 |
| US-304b | in_progress | 2026-08-16 | — | PR #33 (avance independiente ML/agente, Carlos); vence en S5 | 2026-08-17 |
| US-305 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-311 | in_progress | 2026-08-08 | — | [[_DevLog/2026-08-13-hector-morales-entrenamiento-ml01]] · PR #28 (ML-01 entrenado, **MAE 0.0141 / RMSE 0.0177**, TEST-005) · PR #8 · PR #21; MLflow ya alineado a 3.15.1 (PR #45, **BLOCK-001 mitigating**) — falta que Héctor re-corra y confirme el registry end-to-end para cerrar AC-003.4; **objetivo de predicción definido por DEC-007** e **implementado a nivel `municipio × nivel`** (PR #56, `target_hibrido.py`, **TEST-009**, 18 casos) sobre fixture — objetivo real pendiente de la **serie SNIEE** (gate 30-ago). PR #83 generaliza el desglose por entidad que impedía entrenar sobre el grano de DEC-007 | 2026-08-25 |
| US-312 | in_progress | 2026-08-18 | — | [[_DevLog/2026-08-18-hector-morales-evaluacion-us312]] · PR #42 (reporte de evaluación comparativa, TEST-007); **avance parcial** — falta ML-03 (US-321) para cerrar AC-003.2 | 2026-08-18 |
| US-313 | in_review | 2026-08-14 | — | [[_DevLog/2026-08-14-hector-morales-publicacion-gold]] · [[_DevLog/2026-08-23-hector-morales-grano-dual-dec010]] · PR #41 (job batch a `gold.predicciones`, TEST-006, DEC-005) · PR #83 (**grano dual de DEC-010**: discriminador `grano`, CHECK en base y dos índices únicos parciales; 32 casos en `test_publicar_gold`). `in_review` y no `done`: [[15_ML_Models/Publicacion_Gold]] sigue en `status: in_review` y **BUG-010** mantiene `/predicciones` sirviendo `mock_data` | 2026-08-25 |
| US-401 | done | 2026-08-03 | — | [[03_Architecture/API_Specification]] · `api/openapi.v1.json` · [[_DevLog/2026-08-11-christian-ruiz-us401-contrato-api]] · PR #19 (18 pruebas de contrato) | 2026-08-11 |
| US-402 | done | 2026-08-15 | — | [[_DevLog/2026-08-17-christian-ruiz-us402-oauth-jwt]] · [[03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt]] · PR #43 (OAuth2 + JWT access/refresh, `test_auth_jwt` 15 casos) | 2026-08-18 |
| US-403 | in_progress | 2026-08-15 | — | PR #43 (base de RBAC entregada); falta completar los 2 roles del PRD | 2026-08-18 |
| US-404 | in_progress | 2026-08-15 | — | PR #43 (hardening inicial de la API, avance); vence en S4 | 2026-08-18 |
| US-405 | in_progress | 2026-08-07 | — | [[_DevLog/2026-08-07-edgar-andamiaje-faro-web]] · [[03_Architecture/Frontend_Architecture]] (solo andamiaje) | 2026-08-10 |
| US-411 | in_review | 2026-08-20 | — | [[_DevLog/2026-08-20-karla-monter-us411-endpoints-gold]] · PR #59 (endpoints reales sobre Gold, repositorio inyectable y ordenamiento). `in_review` y no `done`: Karla declara 90% en su plan de sprint y `/series` quedó fuera de alcance por decisión propia — falta su confirmación de cierre. **BUG-008** lo hace inalcanzable dentro del contenedor | 2026-08-25 |
| US-501 | done | 2026-08-09 | — | [[08_CICD_DevOps/Cloud_Run_Deploy]] · [[_DevLog/2026-08-09-luis-tellez-us501-cloud-run-deploy]] · PR #13 (URL pública viva) | 2026-08-10 |
| US-502 | done | 2026-08-13 | — | [[_DevLog/2026-08-15-luis-tellez-us502-docker-compose-ml-services]] · PR #34 (MLflow/Superset/ChromaDB con hardening) · PR #35 (docker-compose del ecosistema) | 2026-08-17 |
| US-503 | done | 2026-08-14 | — | [[_DevLog/2026-08-15-luis-tellez-us503-ci-pipeline]] · PR #35 (pipeline CI completo con GitLeaks y pip-audit) | 2026-08-17 |
| US-504 | in_progress | 2026-08-16 | — | PR #34 (hardening de MLflow/Superset/ChromaDB, avance); vence en S4 | 2026-08-17 |
| US-505 | in_progress | 2026-08-16 | — | PR #34 (avance temprano de rollback/observabilidad); vence en S6 | 2026-08-17 |
| US-521a | done | 2026-08-12 | — | [[_DevLog/2026-08-12-alejandro-velazquez-mendoza]] · PR #25 (docker-compose + guía local API/Postgres) | 2026-08-17 |
| US-521b | in_progress | 2026-08-09 | — | [[_Meta/US-521b-guia-ambiente-local]] · [[_DevLog/2026-08-09-edgar-jimenez-setup]] · PR #14 · PR #29 (env DAGs); **verificar si el docker-compose de Airflow/ML ya queda cubierto por el compose del ecosistema (PR #35)** | 2026-08-17 |
| US-521c | in_review | 2026-08-12 | — | PR #23 (inventario de dependencias + ambiente local Superset/agente); falta DevLog para `done` | 2026-08-17 |
| US-522c | in_review | 2026-08-18 | — | PR #49 (contenerización de Superset + resolución de bloqueo de arranque); falta DevLog para `done`. **BUG-004** sigue abierto a su nombre (`psycopg2` ausente en la imagen de Superset) | 2026-08-25 |
| US-523c | done | 2026-08-22 | — | [[08_CICD_DevOps/US-523c-quality-gate]] (`status: done`) · PR #69 (workflow `quality_gate.yml` + plantilla de PR). Operando en todos los PRs desde el 22-ago. Deuda conocida: el workflow no se dispara en `edited`, así que corregir el cuerpo de un PR no vuelve a correr el check | 2026-08-25 |

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
- **S3 adelantadas:** US-202 (Manuel · Superset, PR #39) · US-402 (Christian · OAuth2 + JWT, PR #43).

**`in_review` (core entregado, falta DevLog/trazabilidad o mantenimiento):** US-004 (tablero PM,
continuo) · US-122b (extractores DS-04/05) · US-211a (cubos DB-03/04) · US-521c (ambiente Superset/agente).

**`in_progress`:** US-112/US-113 (Silver→Gold y cubos, Deni, S3) · US-302/303/304a/304b (Andrés/Carlos ·
avance independiente ML/agente, PR #33) · US-403/404 (Christian · RBAC base + hardening, PR #43) ·
US-504/505 (Luis Téllez · hardening/observabilidad, PR #34) · US-521b (Edgar Jiménez · **verificar** si el
compose del ecosistema ya lo cubre) · las cuatro de **FARO Web** (US-206/207/305/405 · solo andamiaje, PR #7).

**🛑 Corrección de US-311 (gap detectado por Héctor, PR #42/#41).** Se **regresa de `done` a
`in_progress`**: aunque PR #28 entrenó el modelo con métricas sólidas, **AC-003.4 no está cumplido** — el
registro en MLflow no funciona porque `docker/mlflow.Dockerfile` corre `mlflow==2.8.0` contra el cliente
`3.15.1`, así que el modelo nunca llega al *registry* (solo se ven las corridas en la UI). Es un
**bloqueo real (BLOCK-001)** que también frena AC-003.4 de US-302/303 (Andrés), US-321 (Estefany) y
US-313. Lo resuelve **Célula 5** (Luis) alineando las versiones. Además, **US-312/US-313** entran como
`in_progress` (avances parciales de Héctor: reporte de evaluación y publicación a Gold).

**⚠️ Hueco real (bloqueo de calendario):** **Emilio Galnares** no ha arrancado su ramo de **DS-06
(CONAGUA) y DS-08 (CONAPO)** — US-121a (prueba, S1), US-122a (extractores, S2) y US-123a (Great
Expectations, S3), todas suyas y encadenadas. Su par Luis E. García ya cerró el ramo simétrico
(DS-04/05). Es el único gap de S2 y arrastra 2 de las 8 fuentes hacia Gold. **Prioridad de destrabe.**

Para US de documentación/diseño, la "prueba" de Definition of Done la cubren la revisión del Tech Lead
responsable, `vault_lint` y TEST-002.
