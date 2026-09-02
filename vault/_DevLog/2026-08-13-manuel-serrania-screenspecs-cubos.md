---
project: "FARO"
date: "2026-08-13"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
session_duration: "sesión única: corrección de Screen_Specs — JOINs a predicciones/recomendaciones y umbral de riesgo"
touches: ["US-201", "REQ-002", "DOC-SCREENSPECS", "DOC-INDICE-RIESGO", "DOC-DATAMODEL", "DOC-TRACE-MATRIX"]
tags: [devlog, dashboards, kpis, celula-2]
---

# DevLog — 2026-08-13 — Corrección Screen_Specs: cubos leen riesgo/driver vía JOIN

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

`Data_Model.md` v2 (ya en `main`) separó los **hechos observados** de las **salidas de ML**:
`fact_escuela_ciclo` ya no contiene `indice_riesgo` ni `driver_dominante` (§4.1: se consultan vía
JOIN por `cct, id_ciclo`). El `Screen_Specs.md` de US-201 (S1) quedó desincronizado: KPI-03, KPI-04,
KPI-07 y KPI-10 leían esas columnas directo del hecho.

En paralelo, Héctor Morales (C3) ancló el `indice_riesgo` de ML-01 con la sigmoide de
`vault/15_ML_Models/Indice_Riesgo_ML01.md` y pidió ratificar el umbral de negocio **0.6 = perder ~5% de
matrícula** (leído del `>= 0.6` del Screen_Specs). El `0.6` lo había fijado el agente en S1 como
"revisable por el negocio", así que requería confirmación.

## Decisiones ratificadas (a registrar por el PM como DEC-005)

1. **Umbral de negocio:** "escuela en riesgo" = `indice_riesgo >= 0.6` ↔ perder ~5% de matrícula.
   Desbloquea que `Indice_Riesgo_ML01.md` pase de `in_review` a `approved`.
2. **Contrato de schema:** `gold.predicciones` conserva `valor` (variación cruda para MAE/RMSE) y
   agrega la columna derivada `indice_riesgo` (0–1, single source `src/modelos/riesgo.py`). Cambio de
   schema = regla 7 → revisión humana de Diana (C1), Andrés/Héctor (C3) y Christian (C4).

## Qué se hizo

- **`vault/04_UX_Design/Screen_Specs.md`** (corrección US-201):
  - KPI-03 y KPI-10 (`cubo_riesgo_territorial`): `f.indice_riesgo` → `p.indice_riesgo` con
    `JOIN gold.predicciones p ON f.cct = p.cct AND f.id_ciclo = p.id_ciclo WHERE p.modelo = 'ML-01'`.
  - KPI-04 (escuelas en riesgo): mismo JOIN; filtro `p.indice_riesgo >= 0.6` + traza del umbral
    ratificado (0.6 = ~5%) a `DOC-INDICE-RIESGO`.
  - KPI-07 (`cubo_driver`): `driver_dominante` vía `JOIN gold.recomendaciones r` + `dim_driver`.
  - §4 intro: regla de lectura (salidas de ML siempre por JOIN; aplica también a `cubo_pivot`).
  - `last_reviewed` → 2026-08-13.
- **DevLog** creado y registrado en `vault/_DevLog/_index.md`.
- **`vault/02_Requirements/Traceability_Matrix.md`**: columna DevLog de REQ-002 → referencia la corrección.
- **Seguimiento §9** del plan de sprint: US-201 → ✅ Terminado, 100%.

## 🤖 Sesión de IA

- **Agente / modelo:** OpenCode / opencode/big-pickle
- **Archivos creados/modificados:**
  - `vault/04_UX_Design/Screen_Specs.md`
  - `vault/_DevLog/2026-08-13-manuel-serrania-screenspecs-cubos.md` (nuevo)
  - `vault/_DevLog/_index.md`
  - `vault/02_Requirements/Traceability_Matrix.md`
  - `vault/12_Roadmap_Sprints/Sprints/2-manuel-alejandro-serrania-reinada.md`
- **Decisiones autónomas del agente:** ninguna — ambas decisiones (umbral y contrato) fueron
  ratificadas por el humano antes de tocar archivos.
- **Pendiente de coordinación (no editado por Manuel):**
  - `vault/03_Architecture/Data_Model.md` §4.5/§5.1 (columna `indice_riesgo`) → Diana (C1).
  - `vault/15_ML_Models/Indice_Riesgo_ML01.md` `in_review` → `approved` → Héctor (C3).
  - `DEC-005` en `vault/10_Risk_Governance/Decision_Log.md` → PM.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [ ] Tests agregados/actualizados (N/A — corrección de documentación de diseño; `pytest tests/` verificado en verde)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes

- Ninguno.

## Próximos pasos

- Revisión del PR por el PM (compuerta única, DEC-003).
- Coordinar con C1/C3/C4 el cambio de contrato de `gold.predicciones`.
- US-202 (S3): configurar Superset — conexión, datasets y capa semántica.
