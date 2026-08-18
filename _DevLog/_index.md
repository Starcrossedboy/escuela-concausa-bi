---
id: MOC-DEVLOG
title: "DevLog Index"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: true
tags: [devlog, index, moc]
---

# DevLog Index — FARO

> **Bitácora ÚNICA** del proyecto (no debe existir otra en la raíz del repo).
> Una entrada por sesión: `YYYY-MM-DD-{nombre}.md` con [[_Templates/DevLog_template]].
> → [[00_Start_Here/PROJECT_INDEX]]

## Regla obligatoria
Toda sesión con IA **debe** generar una entrada de DevLog **antes del push** (parte del
[[05_Engineering/Definition_of_Done]]). Sin sesión de IA, usar `agent: "Manual"`.

## Entradas
| Fecha | Descripción | Autor | Agente/Modelo | IDs tocados |
|---|---|---|---|---|
| 2026-08-01 | (ejemplo) inicialización | Edgar Edmundo Coronel Navarrete | Claude Code | — |
| [[_DevLog/2026-08-02-edgar-edmundo-coronel-navarrete\|2026-08-02]] | Frontmatter PRD-GENERAL, redacción PRD FARO e índice 01_Product | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | PRD-GENERAL, PRD, MOC-01 |
| [[_DevLog/2026-08-03-handoff-planeacion\|2026-08-03]] | **Handoff** de la sesión de planeación (PRD, 7 REQ, 8 fuentes, 87 US, 21 Agent Contexts, Data_Model, AGENTS.md) | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | PRD, REQ-001…007, US-CATALOG, DS-01…08, DOC-DATAMODEL |
| [[_DevLog/2026-08-03-handoff-cierre-planeacion\|2026-08-03]] | **Handoff de CIERRE** de planeación (matriz de trazabilidad + API_Spec + gobernanza + Graphify); siguiente = Bloque E de GitHub | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | DOC-TRACE-MATRIX, DOC-APISPEC, PLAN-MAESTRO |
| [[_DevLog/2026-08-05-edgar-tablero-control-pm-v2\|2026-08-05]] | Tablero PM v2 generado desde fuentes canónicas, automatización, TEST-002 y validación visual | Edgar Edmundo Coronel Navarrete | Codex / GPT-5 | US-004, REQ-007, RPT-PM-SPEC, TEST-002 |
| [[_DevLog/2026-08-06-edgar-directorio-github-codeowners\|2026-08-06]] | Directorio GitHub, Tech Leads en CODEOWNERS y pestaña Equipo trazable con US y PR por integrante | Edgar Edmundo Coronel Navarrete | Codex / GPT-5 | DOC-ONBOARD, US-003, US-004, REQ-007, RPT-PM-SPEC, TEST-002, DEC-002 |
| [[_DevLog/2026-08-06-edgar-swap-celulas-liderazgo-c4\|2026-08-06]] | Re-aplicado swap Eloisa/Oscar, liderazgo C4 (Christian↔Karla) y pestañas Plan general + Foco por sprint | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-003, US-004, US-CATALOG, PLAN-MAESTRO, DOC-ONBOARD, REQ-007, RPT-PM-SPEC, TEST-002 |
| [[_DevLog/2026-08-07-edgar-remediacion-sprint1\|2026-08-07]] | Paquete único de correcciones: issue #4 (lint .venv, URL, requirements, correo), catálogo DB, GitHub de Oscar y pestaña Calendario | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-003, US-004, REQ-007, DOC-ONBOARD, DOC-ENVSETUP, PRD, US-CATALOG, RPT-PM-SPEC, TEST-002 |
| [[_DevLog/2026-08-07-edgar-andamiaje-faro-web\|2026-08-07]] | Andamiaje de FARO Web (Streamlit): 4 US nuevas (91 US), ADR-002, Frontend_Architecture, esqueleto y trazabilidad | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-206, US-207, US-305, US-405, REQ-002, REQ-004, REQ-006, ADR-002, DOC-FRONTEND-ARCH |
| [[_DevLog/2026-08-07-manuel-serrania-us-201\|2026-08-07]] | US-201: portafolio de 10 dashboards (arquitectura de información, árbol de navegación) y catálogo de 14 KPIs con SQL; ratificación catálogo DB del PRD | Manuel Alejandro Serranía Reinada | OpenCode / deepseek-v4-flash-free | US-201, REQ-002, DOC-SCREENSPECS, DOC-TRACE-MATRIX, PRD |
| [[_DevLog/2026-08-07-diana-alvarez-data-model-us101\|2026-08-07]] | Revisión crítica de Data_Model.md: separación de hechos observados y salidas ML en fact_escuela_ciclo | Diana Aracely Alvarez Varela | Claude / sonnet-5 | US-101 |
| [[_DevLog/2026-08-08-hector-morales-fixture-particion-temporal\|2026-08-08]] | Ambiente C3, revisión del onboarding (6 defectos reportados) y andamiaje de US-311: fixture simulado, partición temporal con backtesting y las primeras 15 pruebas del repo | Héctor Rafael Morales Marbán | Claude Code / opus-5 | US-311, REQ-003, TEST-003, DOC-ONBOARD |
| [[_DevLog/2026-08-10-deni-garrido-onboarding\|2026-08-10]] | Onboarding, ambiente local y primer PR de práctica | Deni Garrido Fragoso | Codex / GPT-5 | DOC-ONBOARD |
| [[_DevLog/2026-08-09-andres-gonzalez-vault-lint-windows\|2026-08-09]] | Fix vault_lint.py compatible con Windows: `_norm()` + `EXCLUDED_DIRS` + `.github`; repo actualizado con 9 commits del remoto | Andrés González Habib | GitHub Copilot / claude-sonnet-4-6 | META-RULES |
| [[_DevLog/2026-08-09-andres-gonzalez-us301-estrategia-modelado\|2026-08-09]] | US-301: ADR-003, ML_Strategy, temporal_split, fixtures mock, 5 tests en verde | Andrés González Habib | GitHub Copilot / claude-sonnet-4-6 | US-301, ADR-003, DOC-ML-STRATEGY, REQ-003 |
| [[_DevLog/2026-08-09-luis-tellez-us501-cloud-run-deploy\|2026-08-09]] | Deploy Hello World a Cloud Run: FastAPI + Docker + GCP setup completo + URL pública funcionando (elimina riesgo del 6.0) | Luis Téllez Domínguez | Claude Code / sonnet-4.5 | US-501, REQ-005, DOC-CLOUD-RUN-DEPLOY |
| [[_DevLog/2026-08-09-edgar-compuerta-unica-aprobacion\|2026-08-09]] | Cambio de política de aprobación de PR: de doble compuerta (2) a compuerta única (1, el PM); CODEOWNERS, ruleset, Branching_Strategy, onboarding y 21 planes | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | DEC-003, DOC-DECLOG, DOC-ONBOARD, US-004, REQ-007 |
| [[_DevLog/2026-08-10-edgar-pm-dashboard-check-siempre-corre\|2026-08-10]] | Fix de CI: el check obligatorio "Generar y validar tablero PM" corre en todos los PR (se quita el filtro paths); desbloquea PR de código puro | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, REQ-007, ENG-BRANCHING |
| [[_DevLog/2026-08-10-edgar-cierre-estatus-sprint1\|2026-08-10]] | Cierre de estatus de Sprint 1: US mergeadas a `done` (US-001/002/003/101/201/311), andamiaje FARO Web a `in_progress`; tablero regenerado | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, US-001, US-002, US-003, US-101, US-201, US-311, REQ-007, PLAN-EXEC-STATUS |
| [[_DevLog/2026-08-09-edgar-jimenez-setup\|2026-08-09]] | Setup inicial del ambiente local reproducible (Airflow 8080 / MLflow 5000): guía en `_Meta`, `configuracion.env` y verificación | Edgar Ulises Jiménez López | Manual | US-521b, DOC-US521B-AMBIENTE |
| [[_DevLog/2026-08-10-edgar-higiene-devlog-refresco-estatus\|2026-08-10]] | Higiene del índice DevLog (fila Deni/Héctor malformada) + refresco de estatus: US-301 y US-501 a `done`, US-521b `in_progress`; tablero regenerado | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, US-301, US-501, US-521b, MOC-DEVLOG, PLAN-EXEC-STATUS |
| [[_DevLog/2026-08-10-edgar-gitattributes-union\|2026-08-10]] | `.gitattributes merge=union` para `_DevLog/_index.md` y la matriz de trazabilidad: elimina los conflictos recurrentes de índices append-only | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, ENG-BRANCHING, MOC-DEVLOG, DOC-TRACE-MATRIX |
| [[_DevLog/2026-08-11-hector-morales-indice-riesgo-ml01\|2026-08-11]] | Índice de riesgo de ML-01: define la conversión de variación de matrícula a `indice_riesgo` ∈ [0,1] que consumen la API, los cubos y los tableros; TEST-004 con 16 casos | Héctor Rafael Morales Marbán | Claude Code / opus-5 | US-311, REQ-003, TEST-004, DOC-INDICE-RIESGO, MOC-MLMODELS |
| [[_DevLog/2026-08-13-hector-morales-entrenamiento-ml01\|2026-08-13]] | Entrenamiento y backtesting de ML-01: pipeline completo, MAE 0.0141 ± 0.0012 con walk-forward, baseline por ventana, error por entidad y registro en MLflow; TEST-005 | Héctor Rafael Morales Marbán | Claude Code / opus-5 | US-311, REQ-003, TEST-005, DOC-ML01-ENTRENAMIENTO, ML-01 |
| [[_DevLog/2026-08-14-hector-morales-publicacion-gold\|2026-08-14]] | US-313: job batch que publica `gold.predicciones` con upsert idempotente, verificado contra Postgres real; catálogo prescriptivo y prioridad desde anclas ratificadas; TEST-006 | Héctor Rafael Morales Marbán | Claude Code / opus-5 | US-313, REQ-003, TEST-006, DOC-PUBLICACION-GOLD, DEC-005 |
| [[_DevLog/2026-08-16-hector-morales-mlflow-servidor\|2026-08-16]] | ML-01 contra el MLflow desplegado: **servidor 2.8.0 vs cliente 3.15.1** registra métricas pero pierde los modelos (AC-003.4); preflight de compatibilidad en `mlflow_utils` con mensaje accionable | Héctor Rafael Morales Marbán | Claude Code / opus-5 | US-311, US-313, REQ-003, DOC-ML01-ENTRENAMIENTO, US-502 |
| [[_DevLog/2026-08-17-hector-morales-cierre-bug003\|2026-08-17]] | Cierre de BUG-003 como `not_a_bug` (el fix ya estaba en `main` desde el 13-ago, PR #28) y corrección de BUG-004, mal asignado a C3 siendo de C5 | Héctor Rafael Morales Marbán | Claude Code / opus-5 | BUG-003, BUG-004, US-311, REQ-003 |
| [[_DevLog/2026-08-18-hector-morales-evaluacion-us312\|2026-08-18]] | US-312: evaluación comparativa ML-01/ML-02, curvas por ventana, error por entidad y por cobertura; el reporte se **genera desde el código** para que AC-003.2 sea reproducible; TEST-007 | Héctor Rafael Morales Marbán | Claude Code / opus-5 | US-312, REQ-003, TEST-007, DOC-EVALUACION-MODELOS |
| [[_DevLog/2026-08-11-edgar-dashboard-ejecutivo-360\|2026-08-11]] | Dashboard ejecutivo 360° del PM: 4 pestañas nuevas (exec/roadmap semáforo/performance/PRD), burndown corregido (2 líneas), riesgos con US+fecha, colector de commits; schema 2.3 | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, REQ-007, RPT-PM-SPEC, TEST-002, DOC-RISK-REGISTER |
| [[_DevLog/2026-08-11-christian-ruiz-us401-contrato-api\|2026-08-11]] | US-401: publicación del contrato de la API — `openapi.v1.json` estable, stub FastAPI de referencia (`src/api/`), datos mock sintéticos y 18 pruebas de contrato en verde; desbloquea mocks de C2 y C3 | Christian Imanol Ruiz Hurtado | Claude Code / opus-4-8 | US-401, REQ-004, DOC-APISPEC |
| [[_DevLog/2026-08-11-edgar-dashboard-fase-b-autorefresh\|2026-08-11]] | Fase B del tablero: readiness dinámico (URL viva → confianza 15%), iconos de estatus en el calendario y workflow de auto-refresco en cada push a main (DEC-004) | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, REQ-007, DEC-004, RPT-PM-SPEC |
| [[_DevLog/2026-08-11-edgar-correccion-us311-estatus\|2026-08-11]] | Corrección de trazabilidad (gap del PR #21): US-311 de `done` a `in_progress` — falta el modelo ML-01 entrenado + MAE/RMSE + MLflow | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, US-311, REQ-003, PLAN-EXEC-STATUS |
| [[_DevLog/2026-08-12-alejandro-velazquez-mendoza\|2026-08-12]] | US-521a: Setup local FastAPI + Postgres (docker-compose y guía) | Alejandro Velázquez Mendoza | Antigravity | US-521a, DOC-DEV-API-LOCAL, REQ-007 |
| [[_DevLog/2026-08-12-edgar-calendario-responsable\|2026-08-12]] | Calendario del tablero PM: responsable visible por US (avatar de iniciales + nombre corto), pie de responsables por sprint, `owner_short` en el generador y TEST-002 | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, REQ-007, RPT-PM-SPEC, TEST-002, PLAN-EXEC-STATUS |
| [[_DevLog/2026-08-13-manuel-serrania-screenspecs-cubos\|2026-08-13]] | Corrección de Screen_Specs: cubos leen riesgo/driver vía JOIN a `predicciones`/`recomendaciones` (KPI-03/04/07/10) + ratificación del umbral 0.6 = perder ~5% de matrícula | Manuel Alejandro Serranía Reinada | OpenCode / opencode/big-pickle | US-201, REQ-002, DOC-SCREENSPECS, DOC-INDICE-RIESGO |
| [[_DevLog/2026-08-14-marina-garcia-cubos-db03-db04\|2026-08-14]] | US-211a: contrato semántico de los cubos de DB-03 y DB-04 (métricas, jerarquías, granos), SQL de referencia para US-113, capa semántica en `superset/semantic/` y 28 pruebas que hacen cumplir SIN_DATO≠0 y ML por JOIN | Marina García del Buey | Claude Code / claude-opus-5 | US-211a, REQ-002, DOC-CUBESPEC-DB0304, DOC-TRACE-MATRIX, MOC-04 |
| [[_DevLog/2026-08-14-luis-garcia-us121b-prueba-descarga\|2026-08-14]] | US-121b: prueba de descarga real de DS-04 (SESNSP, bloqueado por login Microsoft/SharePoint, escalado a Tech Lead) y DS-05 (SINAICA, endpoints reales probados en vivo, 287 registros horarios y esquema corregido) | Luis Enrique García Vázquez | Claude Code / sonnet-5 | US-121b, REQ-001, DS-04, DS-05 |
| [[_DevLog/2026-08-15-andres-gonzalez-trabajo-independiente-ml-agente\|2026-08-15]] | Avance independiente C3: guardarraíles del agente, scaffold ML-02 con target proxy temporal, helper MLflow y sincronización de ML_Strategy al contrato vigente | Andrés González Habib | GitHub Copilot | US-302, US-303, US-304a, REQ-003, REQ-006 |
| [[_DevLog/2026-08-15-luis-tellez-us502-docker-compose-ml-services\|2026-08-15]] | US-502: Docker Compose completo con MLflow, Superset y ChromaDB (8 servicios orquestados) + auditoría de seguridad CIS Controls v8 (13 vulnerabilidades identificadas, 7 mitigadas, Score 7.0/10) + threat model completo | Luis Téllez Domínguez | Claude Code / sonnet-4.5 | US-502, REQ-005, SEC-THREAT-MODEL, SEC-CREDENTIALS-POLICY |
| [[_DevLog/2026-08-15-luis-tellez-us503-ci-pipeline\|2026-08-15]] | US-503: Pipeline CI completo con GitLeaks (G5) y pip-audit (G6) — escaneo de secretos en historial Git + detección de vulnerabilidades CVE en dependencias + documentación CI_Quality_Gates actualizada con ejemplos Python (6/8 gates implementados) | Luis Téllez Domínguez | Claude Code / sonnet-4.5 | US-503, REQ-007, US-502 |
| [[_DevLog/2026-08-15-manuel-serrania-kpis-db03-ratificacion-join\|2026-08-15]] | Ratificación del LEFT JOIN a salidas de ML en el grano de escuela (DB-03), alta de KPI-15…KPI-18 en el catálogo canónico (AC-002.4) y convención de capa semántica `superset/semantic/` como estándar US-202 | Manuel Alejandro Serranía Reinada | OpenCode / opencode/big-pickle | US-201, US-211a, REQ-002, DOC-SCREENSPECS, DOC-CUBESPEC-DB0304 |
| [[_DevLog/2026-08-16-manuel-serrania-us202-superset\|2026-08-17]] | US-202 completado: sync end-to-end de Superset (conexión Postgres, datasets DB-03/04, 20 métricas), BUG-003 y BUG-004 (psycopg2 faltante en imagen), verificación de alineación US-211a | Manuel Alejandro Serranía Reinada | OpenCode / big-pickle | US-202, US-211a, REQ-002, BUG-003, BUG-004, DOC-SUPERSET-SETUP, DOC-SCREENSPECS, DOC-CUBESPEC-DB0304 |

| [[_DevLog/2026-08-15-deni-garrido-us111-bronze-silver|2026-08-15]] | US-111: avance Bronze→Silver; configuración dbt, macros, sources y modelos iniciales | Deni Garrido Fragoso | ChatGPT / GPT-5.6 Sol | US-111, REQ-001, DS-01, DS-02, DS-03 |
| [[_DevLog/2026-08-16-deni-garrido-us111-bronze-silver-cierre|2026-08-16]] | US-111: cierre técnico dbt; 8 modelos Silver, 51 tests y compilación global | Deni Garrido Fragoso | ChatGPT / GPT-5.6 Sol | US-111, REQ-001, DS-01–DS-08 |
| [[_DevLog/2026-08-17-edgar-reconciliacion-estatus-s2s3\|2026-08-17]] | Reconciliación del estatus del proyecto contra PR #23–#39: 8 nuevos `done` (US-102/111/121b/202/311/502/503/521a), US-311 cerrada, hueco de Emilio (DS-06/08); tablero regenerado | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, REQ-007, PLAN-EXEC-STATUS, RPT-PM-SPEC, TEST-002 |
| [[_DevLog/2026-08-17-christian-ruiz-us402-oauth-jwt\|2026-08-17]] | US-402: núcleo OAuth2/JWT — config tipada, emisión/validación de access+refresh (HS256 endurecido), `get_current_user`, flujo Google desacoplado, política de rol de mínimo privilegio, ADR-004 y 15 pruebas (suite 157 passed) | Christian Imanol Ruiz Hurtado | Claude Code / opus-4-8 | US-402, REQ-004, ADR-004, DOC-SECMODEL |

## Campos del frontmatter
| Campo | Obligatorio |
|---|---|
| `author_human` | ✅ |
| `agent` | ✅ |
| `model` | recomendado |
| `session_duration` | ✅ |
| `touches` (IDs) | ✅ |
