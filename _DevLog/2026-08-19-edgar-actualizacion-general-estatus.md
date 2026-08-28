---
project: "FARO"
date: "2026-08-19"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "actualización general de estatus para presentación al profesor + RISK-007 (ciclo único 911)"
touches: ["US-004", "US-103", "US-104", "US-105", "US-122b", "US-123b", "US-522c", "US-311", "BLOCK-001", "RISK-007", "PLAN-EXEC-STATUS"]
tags: [devlog, execution, status, risk, presentation]
---

# DevLog — 2026-08-19 — Actualización general de estatus

→ [[_DevLog/_index|Volver al índice]] · [[12_Roadmap_Sprints/Execution_Status]] · [[10_Risk_Governance/Risk_Register]]

## Qué se hizo
Reconciliación del estatus tras la ola de merges #45–#52 (para la presentación al profesor) y registro
de un riesgo sin dueño que Héctor destapó en el PR #51.

**Estados actualizados:**
- **US-103 / US-104 → `done`** (PR #48: esquema estrella Gold + `gold.features_escuela` con drivers reales).
- **US-105 → `done`** (PR #52: interpolación IDW de D6 + cobertura parcial e índice de confianza).
- **US-122b → `done`** (PR #47: extractor real de DS-05 SINAICA contra API en vivo).
- **US-123b → `in_progress`** (PR #47: Great Expectations DS-04/05).
- **US-522c → `in_review`** (PR #49: contenerización de Superset).
- **US-311:** MLflow ya alineado a `3.15.1` (PR #45) → **BLOCK-001 a `mitigating`**; falta que C3
  re-corra y confirme el registry end-to-end para cerrar AC-003.4.
- **Hito:** `dbt/models/gold/` ya tiene modelos reales (dim_escuela, fact_escuela_ciclo, features_escuela).

## Riesgo sin dueño → asignado al PO (RISK-007)
Héctor señaló en el PR #51 que el **Formato 911 solo tiene el ciclo 2024-2025**; sin ≥2 ciclos no hay
`target_variacion_matricula` que predecir. Es el supuesto central del proyecto. Se registra **RISK-007**
(prob 4 / impacto 5, dueño Edgar): conseguir un 2º ciclo histórico del 911 o redefinir el target/alcance
del piloto; vence en el gate ML (S4, 30-ago).

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅.
