---
project: "FARO"
date: "2026-08-12"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "mejora del Calendario del tablero PM: responsable visible por US (avatar + nombre corto)"
touches: ["US-004", "REQ-007", "RPT-PM-SPEC", "TEST-002", "PLAN-EXEC-STATUS"]
tags: [devlog, dashboard, calendar, traceability, us-004]
---

# DevLog — 2026-08-12 — Responsable visible en el Calendario

→ [[_DevLog/_index|Volver al índice]] · [[13_Reports/PM_Dashboard_Spec]] · [[12_Roadmap_Sprints/Execution_Status]]

## Qué se hizo
Incremento de **US-004** (tablero de control del proyecto): en la pestaña **Calendario** cada historia
ahora muestra **quién la lleva** de un vistazo, no solo en el *hover*.

- **`generate_pm_dashboard.py`** — nueva función `short_name()` y campo `owner_short` en cada US
  (`parse_stories`): *primer nombre + inicial del primer apellido*. Desambigua a los dos Edgar
  (`Edgar C.` vs `Edgar J.`).
- **`TABLERO_CONTROL_PM.template.html`** — render del `#sprint-board`: chip con **avatar de iniciales
  coloreado por célula** + punto de estado + ID + nombre corto (con recorte `…`), pie
  **"Responsables del sprint"** por columna y nota en la leyenda.
- **`validate_pm_dashboard.py`** (TEST-002) — aserción de que toda US trae `owner_short`.
- `Execution_Status.md` — evidencia de US-004 actualizada (sigue `in_review`, artefacto de
  mantenimiento continuo hasta la demo).

## Por qué
La misión de US-004 es que el tablero sea el **centro de control** legible para el equipo y el
profesor. Ver el responsable directamente en el calendario acelera la lectura de carga por persona y
sprint sin abrir otra pestaña. Todo es **proyección generada** desde fuentes canónicas (DEC-001): el
dato `owner` ya existía, solo se hizo visible.

## Verificación
- `generate` ✅ (91 US, 21 personas) · `validate` (TEST-002) ✅ · `vault_lint` ✅.
- Render revisado en el navegador: 247 avatares, chips con responsable, pie de responsables por sprint;
  `Edgar C.` / `Edgar J.` distinguidos.

## Decisión de estatus
US-004 se mantiene **`in_review`** (no `done`): su objetivo es "actualizada en cada standup" hasta la
demo del 9-sep; cerrarla afirmaría que ya no se toca. En el tablero pondera 0.65, no penaliza.
