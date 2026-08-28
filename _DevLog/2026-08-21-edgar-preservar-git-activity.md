---
project: "FARO"
date: "2026-08-21"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "hardening del generador: preservar git_activity al regenerar sin token (observación de Marina)"
touches: ["US-004", "REQ-007", "META-RULES", "RPT-PM-SPEC"]
tags: [devlog, dashboard, tooling, engagement]
---

# DevLog — 2026-08-21 — Preservar git_activity al regenerar sin token

→ [[_DevLog/_index|Volver al índice]] · [[13_Reports/PM_Dashboard_Spec]]

## Contexto
Marina observó que cualquier PR que regenera el tablero **en local sin token de GitHub** deja
`git_activity` en `{available:false, prs:[]}`, lo que vacía la pestaña **Engagement** (se alimenta del
historial de PRs). Fase B lo reparaba al mergear, pero el estado degradado viajaba en el PR.

## Qué se hizo
- **`generate_pm_dashboard.py` → `load_github_activity()`**: si la recolección no está disponible
  (regenerado local sin token), en vez de dejar el bloque vacío **conserva el último `git_activity`
  publicado en `13_Reports/data/pm-dashboard.json`** (reutiliza el bloque solo si `available` y con PRs).
  Fase B lo sigue repoblando con datos frescos al mergear (`refresh-dashboard.yml` con el PAT).

## Por qué no rompe el CI
El check `pm-dashboard.yml` recolecta con `GITHUB_TOKEN`, regenera y valida **en CI** (no hace `git diff`
contra el archivo commiteado), así que el fallback local no altera el gate.

## Verificación
- Regenerado en local (sin `github-activity.json`): `git_activity` pasó de vaciarse a **conservar los 60
  PRs** (`available: true`). Diff del JSON = solo metadata de generación; `git_activity` intacto.
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅.
