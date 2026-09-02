---
project: "FARO"
date: "2026-08-11"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "dashboard ejecutivo 360° del PM: nuevas pestañas, burndown corregido, performance y riesgos"
touches: ["US-004", "REQ-007", "RPT-PM-SPEC", "TEST-002", "DOC-RISK-REGISTER"]
tags: [devlog, dashboard, pm, executive, risks, performance]
---

# DevLog — 2026-08-11 — Dashboard ejecutivo 360° del PM

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/13_Reports/PM_Dashboard_Spec]] · [[vault/12_Roadmap_Sprints/Execution_Status]]

## Qué se hizo (Fase A — presentable para la demo)
Se amplió el Tablero de Control PM con una capa ejecutiva "state of the art", todo generado desde
fuentes canónicas (DEC-001):

- **4 pestañas nuevas** en `TABLERO_CONTROL_PM.template.html`:
  - **Ejecutivo 360°** (pestaña estrella): semáforo por módulo de la rúbrica, avance ponderado,
    burndown corregido, cumplimiento del PRD del profesor, **mapa de calor de riesgos**, tabla de
    riesgos críticos (US · dueño · P×I · fecha objetivo) y **pendientes en turno**.
  - **Roadmap semáforo** (progreso por sprint), **Performance equipo** (heatmap integrante × sprint +
    engagement) y **Cumplimiento PRD** (7 criterios: diseño vs. ejecución).
- **Burndown corregido:** antes quedaba plano (solo contaba `done`). Ahora grafica dos líneas —
  restantes por Done **y** por avance ponderado (`weighted_remaining`) — y se mueve con el trabajo en
  curso. Causa raíz documentada.
- **Riesgos enriquecidos:** `Risk_Register.md` gana columnas **US relacionada** y **Fecha objetivo de
  mitigación**; el generador y las tablas del tablero las exponen. RISK-001 (URL pública) → `cerrado`.
- **Generador (`generate_pm_dashboard.py`):** bloques nuevos `performance`, `pending`,
  `prd_compliance`, banda de semáforo en `rubric`, `weighted_remaining` en el historial; schema 2.3.
- **Colector (`collect_github_activity.py`):** ahora recopila **commits por autor** (engagement de
  toda la trazabilidad); se activa cuando corre en CI con token.
- **Validador (`validate_pm_dashboard.py`, TEST-002):** contrato ampliado (bloques nuevos, bandas,
  4 pestañas nuevas, 91 US).

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅.
- Render en navegador sin errores de consola; el Ejecutivo 360° muestra semáforo, burndown de 2 líneas,
  PRD (REQ-005 "URL pública viva"), mapa de calor y riesgos con US/dueño/fecha.

## Pendiente (Fase B — fast-follow, requiere Luis)
Workflow `refresh-dashboard.yml` para regenerar y **commitear** el tablero en cada push a `main` +
bypass del bot de Actions en el ruleset (cambio de CI/seguridad, regla 7). Irá en un PR aparte con
revisión de C5 y su `DEC-###`.
