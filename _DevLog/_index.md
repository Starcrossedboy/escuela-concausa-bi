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

## Campos del frontmatter
| Campo | Obligatorio |
|---|---|
| `author_human` | ✅ |
| `agent` | ✅ |
| `model` | recomendado |
| `session_duration` | ✅ |
| `touches` (IDs) | ✅ |
