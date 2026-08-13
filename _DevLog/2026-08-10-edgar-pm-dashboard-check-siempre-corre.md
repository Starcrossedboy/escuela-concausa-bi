---
project: "FARO"
date: "2026-08-10"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "fix de CI: el check obligatorio 'Generar y validar tablero PM' corre en todos los PR"
touches: ["US-004", "REQ-007", "ENG-BRANCHING"]
tags: [devlog, ci, github-actions, ruleset, fix]
---

# DevLog — 2026-08-10 — el check "PM Dashboard" corre en todos los PR

→ [[_DevLog/_index|Volver al índice]] · [[08_CICD_DevOps/_index]] · [[05_Engineering/Branching_Strategy]]

## Problema
El check **"Generar y validar tablero PM"** (workflow `pm-dashboard.yml`) es **requerido** por el ruleset
de `main`, pero su disparador `pull_request` tenía un filtro `paths:`. Todo PR que **no** tocara esas
rutas (p. ej. código puro de ML/API/agente/frontend, o el fix de `vault_lint.py`) **nunca disparaba el
check** → GitHub lo dejaba en "pending" → **el PR no se podía mergear jamás**. Esto bloqueaba a #11, #12,
#14 y a cualquier PR futuro de código.

## Cambio
Se quita el filtro `paths:` del disparador `pull_request` en `.github/workflows/pm-dashboard.yml`, de
modo que el check **corre en todos los PR** y siempre reporta estado. El job regenera el tablero desde
las fuentes canónicas (intactas en cualquier rama), así que pasa aunque el PR no toque el tablero. El
disparador `push` a `main` conserva su filtro de rutas (no aporta correr en cada push).

## Verificación
- `vault_lint.py` en verde.
- Tras el merge, los PR que antes quedaban con un solo check ahora muestran los **dos** checks
  requeridos y pueden mergear.

## Nota de gobernanza
Cambio de CI/CD → requiere revisión humana explícita (regla 7 del vault): lo revisa Célula 5 (Luis
Téllez), dueño de `.github/`.
