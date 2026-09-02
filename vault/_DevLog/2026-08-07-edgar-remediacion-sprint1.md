---
project: "FARO"
date: "2026-08-07"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "paquete único de correcciones de Sprint 1 (issue #4 + reporte de C2 + directorio)"
touches: ["US-003", "US-004", "REQ-007", "DOC-ONBOARD", "DOC-ENVSETUP", "PRD", "US-CATALOG", "RPT-PM-SPEC", "TEST-002"]
tags: [devlog, onboarding, correcciones, dashboard, governance]
---

# DevLog — 2026-08-07 — paquete único de correcciones (Sprint 1)

→ [[vault/_DevLog/_index|Volver al índice]] · [Issue #4](https://github.com/edgarcoroneln/escuela-concausa-bi/issues/4)

## Qué se hizo (un solo PR)

Atiende el [issue #4](https://github.com/edgarcoroneln/escuela-concausa-bi/issues/4) de Héctor Morales, el
reporte de una compañera de C2 (catálogo de dashboards) y el cierre del directorio de GitHub:

- **P0** GitHub de Oscar Quiroz → `oscarqlazaro-lab` (21/21 confirmados; cero pendientes).
- **P1 🔴** `vault_lint.py` ahora excluye `.venv/`, `venv/`, `node_modules/`, `.pytest_cache/`,
  `.ruff_cache/`, `__pycache__/` (vía `EXCLUDED_DIRS`). Antes, crear el venv dentro del repo metía 52
  falsos positivos y nadie podía marcar el checklist de DoD.
- **P2 🟠** Reemplazo de la URL de clonado inexistente `faro-escuela-sensor` → `escuela-concausa-bi`
  en **23 archivos** (21 planes + Plan Maestro + Agent Context del PO).
- **P3 🟡** Convención `pip freeze > requirements/celula-{n}.txt` en los 21 planes + carpeta
  `requirements/` con README + 5 líneas en `CODEOWNERS` (un revisor por célula).
- **P4 🟡** §4.1 de los 21 planes: correo **verificado en GitHub** (no institucional) + verificación
  `git log -1 --format='%an <%ae>'` en el checklist de entrega (evita commits sin atribuir → módulo 7).
- **P5 🟢** Nota de stacks en `requirements.txt` y `brew install libomp` en los 4 planes de C3 (xgboost/macOS).
- **P6** `CODEOWNERS` de C4 (`/src/api/`, `/07_Security/`) de Karla → **Christian** (`@ImanolRuiz00`),
  alineando con el swap de liderazgo.
- **P7 🟢** `Environment_Setup.md` marcado como complementario del canónico `Developer_Onboarding`
  (regla 1) y con la tabla de comandos llena.
- **P8** Catálogo de los 10 dashboards en `PRD.md §12` homologado con `User_Stories.md`/fichas de C2
  (versión vigente). **Pendiente de ratificación de Manuel (TL C2).**
- **P9** Nueva pestaña **Calendario / Roadmap** en el tablero (línea de tiempo de sprints con hitos
  CODE FREEZE y demo + tablero por sprint con las 87 historias coloreadas por célula).

`docker-compose.yml` (Héctor #6a) queda como entregable de C5 (US-502), no del PM.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code / opus-4-8.
- **Método:** ediciones puntuales + script para los cambios masivos en los 21 planes; red de seguridad del pipeline.
- **Decisiones:** homologar el catálogo DB al de User_Stories (vigente en ejecución) sin inventar
  propósitos, dejándolo pendiente de ratificar con Manuel; no destazar el bloque `git clone` de los 21
  planes (solo corregir la URL) para no desestabilizarlos.

## Verificación
- `generate_pm_dashboard.py` → 87 US · `validate_pm_dashboard.py` → ✅ TEST-002 · `vault_lint.py` → ✅.
- **P1 probado:** lint **verde con un `.venv` presente** (con un LICENSE.md dentro).
- `grep faro-escuela-sensor` = 0.
- Pestaña Calendario verificada en navegador (6 sprints + demo, hitos, 87 chips) sin errores de consola.

## Fuera de este paquete
- **Capa web integrada (Streamlit)** — desarrollo nuevo, va en su propio track (PR de andamiaje + PRs por US).
