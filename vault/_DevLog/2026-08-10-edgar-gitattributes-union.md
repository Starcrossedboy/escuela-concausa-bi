---
project: "FARO"
date: "2026-08-10"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "gitattributes merge=union para índices append-only"
touches: ["US-004", "ENG-BRANCHING", "MOC-DEVLOG", "DOC-TRACE-MATRIX"]
tags: [devlog, git, ci, housekeeping]
---

# DevLog — 2026-08-10 — .gitattributes merge=union

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/05_Engineering/Branching_Strategy]]

## Qué se hizo
Se agregó `.gitattributes` en la raíz con `merge=union` para los dos archivos que provocaban
conflictos en cada PR (todos agregan una fila):

- `vault/_DevLog/_index.md`
- `vault/02_Requirements/Traceability_Matrix.md`

## Por qué
Durante el cierre de PRs de Sprint 1 (#8–#17) estos índices chocaron en casi todos los merges y hubo
que resolverlos a mano por unión (una vez incluso quedó una fila malformada). El driver integrado
`merge=union` de Git conserva ambos lados automáticamente — Git localmente y GitHub en el merge del PR
lo respetan. Elimina el conflicto recurrente para registros de solo-agregado.

## Nota
Si dos PR editaran la **misma** fila ya existente, `union` duplicaría; ese caso raro se revisa a mano.

## Verificación
- `vault_lint.py` ✅ (`.gitattributes` no es `.md`, no afecta al vault).
