---
project: "FARO"
date: "2026-08-19"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "cierre de RISK-004, RISK-002 a mitigando y coloreo por estado en el tablero"
touches: ["US-004", "REQ-007", "DOC-RISK-REGISTER", "RPT-PM-SPEC", "TEST-002"]
tags: [devlog, risk, dashboard, ui]
---

# DevLog — 2026-08-19 — Cierre de riesgos cubiertos + coloreo por estado

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/10_Risk_Governance/Risk_Register]]

## Qué se hizo
Higiene del registro de riesgos tras la entrega de Gold, y corrección visual del tablero.

- **RISK-004 (retraso de Gold) → `cerrado`**: US-103/104/105 quedaron `done` (PR #48/#52); Gold real
  entregado (dim/fact + `features_escuela`). Ya no bloquea BI/ML/API.
- **RISK-002 (fuentes inservibles) → `mitigando`** (no `cerrado`): DS-04/05 probadas con extractor real
  (PR #47) y DS-01/02/03/07 vía DAG, pero **DS-06 (CONAGUA) y DS-08 (CONAPO) siguen sin prueba real**
  (Emilio, US-121a/122a en `planned`). Se documenta el faltante en la fila.
- **RISK-001** ya estaba `cerrado` (URL viva) — sin cambio.
- **Fix de UI:** el tablero no tenía clases CSS para los estados de riesgo, así que los `cerrado` no se
  veían verdes. Se agregan `.pill.cerrado/.resolved` (verde), `.pill.mitigando/.mitigating` (ámbar) y
  `.pill.abierto/.open` (rojo) en `TABLERO_CONTROL_PM.template.html`.

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅.
- Render revisado en el navegador: RISK-001/004 en **verde**, mitigando en ámbar, abierto en rojo.

## Nota
No se cerró RISK-002 pese a la petición, porque 2 de 8 fuentes aún no tienen prueba real — cerrarlo
sería declarar cubierto algo que no lo está. Queda `mitigando` con el faltante visible.
