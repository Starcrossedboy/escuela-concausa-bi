---
project: "FARO"
date: "2026-08-09"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "cambio de política de aprobación de PR: de doble compuerta a compuerta única (PM)"
touches: ["DEC-003", "DOC-DECLOG", "DOC-ONBOARD", "US-004", "REQ-007"]
tags: [devlog, governance, codeowners, ruleset, decision]
---

# DevLog — 2026-08-09 — compuerta única de aprobación (PM)

→ [[_DevLog/_index|Volver al índice]] · [[10_Risk_Governance/Decision_Log]] · [[05_Engineering/Branching_Strategy]]

## Qué se hizo
Se cambió la **política canónica de aprobación de PR** de **doble compuerta** (Tech Lead + PM, 2
aprobaciones) a **compuerta única**: el **PM (`@edgarcoroneln`) es el único aprobador obligatorio** de
todo el repositorio (**DEC-003**). Motivo: en Sprint 1 la 2ª aprobación bloqueó PR ya listos.

### Cambios de documentación (este PR)
- **`.github/CODEOWNERS`** — reducido a `* @edgarcoroneln` (PM = único dueño). Se retiran los Tech Leads
  por carpeta; siguen revisando de forma **no bloqueante** (se les solicita con *Reviewers*).
- **`10_Risk_Governance/Decision_Log.md`** — nueva entrada **DEC-003** (deja sin efecto la doble compuerta).
- **`05_Engineering/Branching_Strategy.md`** — sección "doble compuerta" reescrita a "compuerta única";
  checklist del PM y sección de protección de `main` actualizadas (1 aprobación + bypass admin).
- **`00_Start_Here/Developer_Onboarding.md`** — flujo de trabajo y nota de CODEOWNERS.
- **`AGENTS.md`** — regla de PR.
- **`.github/PULL_REQUEST_TEMPLATE.md`** — bloque de aprobación.
- **21 planes de sprint** — "2 aprobaciones" → "1 aprobación (PM)".

### Cambio de configuración (fuera del PR — lo aplica el PM en GitHub)
En el ruleset `main`: `required_approving_review_count: 2 → 1`, `require_code_owner_review: true` (se
mantiene), y **bypass del rol Repository admin** para que el PM pueda mergear sus propios PR (no puede
autoaprobarlos).

## Por qué
La doble aprobación obligatoria demostró ser un cuello de botella operativo (PR #8/#9/#10 esperando 2ª
firma). El PM asume proceso + trazabilidad; la revisión técnica del Tech Lead se conserva como apoyo.

## Nota de gobernanza
Cambio de CI/CD y seguridad → requiere revisión humana explícita (regla 7 del vault). El propio PR es el
punto de revisión; el ruleset lo aplica el PM manualmente en Settings.
