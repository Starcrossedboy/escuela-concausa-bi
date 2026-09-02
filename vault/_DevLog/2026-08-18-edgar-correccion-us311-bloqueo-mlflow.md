---
project: "FARO"
date: "2026-08-18"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "corrección de US-311 (gap MLflow) + alta de US-312/313/402/403/404 + BLOCK-001"
touches: ["US-004", "US-311", "US-312", "US-313", "US-402", "US-403", "US-404", "BLOCK-001", "PLAN-EXEC-STATUS", "DOC-BLOCKERREG"]
tags: [devlog, execution, status, blocker, mlflow, correction]
---

# DevLog — 2026-08-18 — Corrección US-311 y bloqueo de MLflow

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/12_Roadmap_Sprints/Execution_Status]] · [[vault/10_Risk_Governance/Blocker_Register]]

## Qué se hizo
Héctor destapó en su PR #42 un **gap real** en la reconciliación previa: **US-311 estaba `done`**
citando "MLflow", pero el registro **no funciona**. Verificado en el repo:
`docker/mlflow.Dockerfile` corre `mlflow==2.8.0` contra el cliente `requirements/celula-3.txt`
`3.15.1`; las corridas se ven en la UI pero el modelo **nunca llega al registry** → **AC-003.4 no
cumplido**.

- **US-311 `done` → `in_progress`** con la salvedad de AC-003.4 y referencia a **BLOCK-001**.
- **Alta de BLOCK-001** en `Blocker_Register.md` (proveedor C5, consumidor C3; frena US-302/303/321/313).
- **Alta de estados** por PRs recién mergeados:
  - US-312 `in_progress` (PR #42, TEST-007; parcial, falta ML-03).
  - US-313 `in_progress` (PR #41, TEST-006, DEC-005; falta `gold.recomendaciones` vía ML-02).
  - US-402 `done` (PR #43, ADR-004, `test_auth_jwt` 15 casos).
  - US-403 `in_progress` (base RBAC) · US-404 `in_progress` (hardening inicial).

## Por qué
El tablero es la cara del proyecto ante el profesor: no puede afirmar `done` sobre un AC que no está
cumplido. La corrección es honesta y deja el bloqueo visible y con dueño (Luis, C5).

## Delegaciones abiertas (mensajes enviados por el PO)
- **Luis (C5):** alinear MLflow — subir el servidor a `3.15.1` y validar el registro end-to-end (BLOCK-001).
- **Andrés (C3):** alinear umbrales de ML-01 (`ML_Strategy §5` en alumnos absolutos vs contrato en
  variación) y consolidar el catálogo de recomendaciones (3 módulos).

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅.
