---
project: "FARO"
date: "2026-08-11"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "corrección de trazabilidad: US-311 de done a in_progress (gap detectado en PR #21)"
touches: ["US-004", "US-311", "REQ-003", "PLAN-EXEC-STATUS"]
tags: [devlog, execution, status, correction, traceability]
---

# DevLog — 2026-08-11 — Corrección de estatus de US-311

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/12_Roadmap_Sprints/Execution_Status]]

## Qué se hizo
Se corrigió un **gap de trazabilidad** que Héctor destapó en su PR #21: `Execution_Status.md` marcaba
**US-311 como `done`** desde el cierre de Sprint 1, pero el PR #8 fue avance parcial (fixture +
partición temporal) y el PR #21 (índice de riesgo) también es parcial. **Falta el entregable central**
de la historia: el modelo **ML-01 entrenado + MAE/RMSE + registro en MLflow** (AC-003.2/003.4),
bloqueado por US-104 (C1); vence en S4 (30-ago).

- **US-311: `done` → `in_progress`** en `Execution_Status.md` (tabla + interpretación).
- Tablero regenerado en consecuencia.

## Por qué
El estatus lo cerré yo por error en el bulk de Sprint 1 tomando el PR #8 como evidencia; el tablero
debe reflejar que el modelo aún no existe. El PR #21 aporta el contrato del índice de riesgo pero no
cierra US-311.

## Pendiente relacionado (no en este PR)
- Fusionar las dos implementaciones de partición temporal (`particion_temporal.py` #8 vs
  `utils/temporal_split.py` #12) y versionar el fixture `.parquet` (4 tests en skip). Héctor ofrece PR.

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅.
