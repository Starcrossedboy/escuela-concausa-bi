---
project: "FARO"
date: "2026-08-21"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "cierre US-211a + registro DEC-008 (grano DB-04) + fix Windows de vault_lint (revisión de Marina)"
touches: ["US-211a", "DEC-008", "DOC-DATAMODEL", "META-RULES", "REQ-002", "US-004"]
tags: [devlog, governance, dbt, cubos, vault-lint]
---

# DevLog — 2026-08-21 — Cierre US-211a, DEC-008 y fix de vault_lint

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/10_Risk_Governance/Decision_Log]] · [[vault/03_Architecture/Data_Model]]

## Contexto
Revisión de Marina García al cerrar **US-211a** (cubos DB-03/DB-04). Levantó 5 puntos; se validaron todos
contra el repo y se atienden aquí (3 estaban resueltos por el trabajo de gobernanza reciente).

## Qué se hizo
1. **US-211a → `done`** (Execution_Status): 100%, PR de cierre aprobado, [[vault/_DevLog/2026-08-21-marina-garcia-cierre-us211a]].
2. **`DEC-008` registrado** (Decision_Log): cambio de grano de `gold.cubo_comparador_municipio`
   (`municipio × ciclo` → `municipio × nivel × ciclo`, métricas como numerador/denominador por separado).
   Decisión de esquema de Diana (14-ago, regla 7) que [[vault/03_Architecture/Data_Model]] §4.3 marcaba como
   "pendiente de registrar". **Nota:** Marina sugirió `DEC-007`, pero ese número ya es el target híbrido tras
   la resolución de la colisión; el libre era **DEC-008**.
3. **Referencia cruzada corregida** (Data_Model §4.3): la nota citaba `(DEC-005)` para el principio de
   medidas aditivas de `fact_escuela_ciclo`, pero DEC-005 es el contrato de schema de `gold.predicciones`.
   Se quitó la cita (el principio de facts es diseño del propio Data_Model) y se cerró la traza con DEC-008.
4. **`vault_lint.py` — fix Windows** (`vault/_Meta/`): las consolas cp1252 lanzaban `UnicodeEncodeError` al imprimir
   los emoji del reporte. Se fuerza `sys.stdout/stderr.reconfigure(encoding="utf-8", errors="replace")` con
   guarda; no cambia el resultado del lint, solo la impresión.

## Ya estaba resuelto (puntos 4-anterior y 5 de Marina)
- **`merge=union` duplicaba filas de la matriz:** ya se retiró la matriz de `merge=union` (queda solo el
  DevLog index) en el PR de gobernanza. Verificado: **una sola fila por REQ-001…007** en `main`.

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅.
