---
project: "FARO"
date: "2026-08-19"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "nueva pestaña de Engagement del equipo (quién ha trabajado y quién no)"
touches: ["US-004", "REQ-007", "RPT-PM-SPEC", "TEST-002", "PLAN-EXEC-STATUS"]
tags: [devlog, dashboard, engagement, team]
---

# DevLog — 2026-08-19 — Pestaña de Engagement del equipo

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/13_Reports/PM_Dashboard_Spec]]

## Qué se hizo
Nueva pestaña **Engagement** en el tablero PM: muestra, con evidencia real, **quién ha contribuido y
quién no**, en dos columnas (han trabajado / sin actividad registrada).

- **`generate_pm_dashboard.py`** — `parse_devlog_authors()` (cuenta DevLogs por autor canónico,
  protegiendo los pipes escapados `\|` de los wikilinks) + `build_engagement()`: por persona,
  `active` = tiene PR mergeado **o** DevLog firmado **o** US propia en estado activo (≠ planned). Señal
  offline-safe (no depende del token de GitHub). Schema **2.3 → 2.4**.
- **`TABLERO_CONTROL_PM.template.html`** — pestaña `engagement` + panel de dos columnas con avatar de
  iniciales, célula y señal por persona; coloreo del CSS de estados de riesgo reutilizado.
- **`validate_pm_dashboard.py`** (TEST-002) — schema 2.4; exige `engagement` con 21 personas,
  `active`+`inactive` = total, y el panel `engagement`.
- **`PM_Dashboard_Spec.md`** — fila de la pestaña + versión 2.4.

## Resultado
- **14 de 21 integrantes con evidencia real · 7 sin actividad registrada** (Emilio, Monserrat, Oscar,
  Estefany, Eloisa, Juan Carlos, Karla).
- Nota: los comentarios/revisiones (p. ej. la revisión de Karla a US-411) **no** cuentan como
  entregable; el Engagement mide contribución comprometida (PR/DevLog/US activa).

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅ · pestaña revisada en el navegador.
