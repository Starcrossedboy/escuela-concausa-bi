---
project: "FARO"
date: "2026-08-11"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "Fase B: auto-refresco del tablero PM + readiness dinámico + iconos de calendario"
touches: ["US-004", "REQ-007", "DEC-004", "RPT-PM-SPEC"]
tags: [devlog, dashboard, ci, github-actions, readiness]
---

# DevLog — 2026-08-11 — Dashboard Fase B: auto-refresco y datos vivos

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/10_Risk_Governance/Decision_Log]] · [[vault/13_Reports/PM_Dashboard_Spec]]

## Qué se hizo
- **Fix de datos "muertos":** los gates de *readiness* estaban hardcodeados en `False`; ahora se
  derivan del estado real de las US (la URL pública se enciende con `US-501` → confianza 15%, antes 0%).
  Desaparece la alerta falsa "URL pública sin evidencia".
- **Calendario por sprint:** cada US se marca con **icono de estatus** (verde Done / ámbar en curso /
  rojo sin iniciar-bloqueada) + leyenda.
- **Fase B · auto-refresco (`refresh-dashboard.yml`):** en cada push a `main` que toque una fuente
  canónica, el workflow regenera y commitea el tablero (HTML + snapshot + historial + actividad). Deja
  todos los reportes "vivos" sin correr el generador a mano. **DEC-004.**

## Activación pendiente (manual, requiere admin + Luis)
El push del bot a `main` está protegido por el ruleset. Para que aterrice:
1. Crear un **PAT fine-grained** (admin, `contents:write` en este repo) y guardarlo como secreto
   **`DASHBOARD_PAT`** (Settings → Secrets and variables → Actions).
2. Confirmar el bypass del ruleset para admin (ya existe por DEC-003).
Sin el secreto, el workflow corre pero no commitea (no falla): el tablero sigue refrescándose en cada PR.
Revisión de CI/seguridad: **Célula 5 (Luis)** (regla 7).

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅ · render sin errores de consola.
