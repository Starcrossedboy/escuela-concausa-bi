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
| [[_DevLog/2026-08-11-edgar-dashboard-ejecutivo-360\|2026-08-11]] | Dashboard ejecutivo 360° del PM: 4 pestañas nuevas (exec/roadmap semáforo/performance/PRD), burndown corregido (2 líneas), riesgos con US+fecha, colector de commits; schema 2.3 | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, REQ-007, RPT-PM-SPEC, TEST-002, DOC-RISK-REGISTER |
| [[_DevLog/2026-08-11-christian-ruiz-us401-contrato-api\|2026-08-11]] | US-401: publicación del contrato de la API — `openapi.v1.json` estable, stub FastAPI de referencia (`src/api/`), datos mock sintéticos y 18 pruebas de contrato en verde; desbloquea mocks de C2 y C3 | Christian Imanol Ruiz Hurtado | Claude Code / opus-4-8 | US-401, REQ-004, DOC-APISPEC |
| [[_DevLog/2026-08-11-edgar-dashboard-fase-b-autorefresh\|2026-08-11]] | Fase B del tablero: readiness dinámico (URL viva → confianza 15%), iconos de estatus en el calendario y workflow de auto-refresco en cada push a main (DEC-004) | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, REQ-007, DEC-004, RPT-PM-SPEC |
| [[_DevLog/2026-08-11-edgar-correccion-us311-estatus\|2026-08-11]] | Corrección de trazabilidad (gap del PR #21): US-311 de `done` a `in_progress` — falta el modelo ML-01 entrenado + MAE/RMSE + MLflow | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, US-311, REQ-003, PLAN-EXEC-STATUS |
| [[_DevLog/2026-08-12-edgar-calendario-responsable\|2026-08-12]] | Calendario del tablero PM: responsable visible por US (avatar de iniciales + nombre corto), pie de responsables por sprint, `owner_short` en el generador y TEST-002 | Edgar Edmundo Coronel Navarrete | Claude Code / opus-4-8 | US-004, REQ-007, RPT-PM-SPEC, TEST-002, PLAN-EXEC-STATUS |

## Campos del frontmatter
| Campo | Obligatorio |
|---|---|
| `author_human` | ✅ |
| `agent` | ✅ |
| `model` | recomendado |
| `session_duration` | ✅ |
| `touches` (IDs) | ✅ |
