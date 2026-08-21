---
project: "FARO"
date: "2026-08-19"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-4-8"
session_duration: "mitigación de RISK-007 + resolución de la colisión de ID DEC-005 y de-dup de la matriz (revisión de PR #56)"
touches: ["RISK-007", "DEC-005", "DEC-006", "DEC-007", "DS-01", "US-104", "US-311", "REQ-002", "REQ-003"]
tags: [devlog, risk, ml, target, data-source]
---

# DevLog — 2026-08-19 — Mitigación de RISK-007 (target de ML)

→ [[_DevLog/_index|Volver al índice]] · [[10_Risk_Governance/Risk_Register]] · [[10_Risk_Governance/Decision_Log]]

## Contexto
RISK-007: el Formato 911 solo se descargó con el ciclo **2024-2025**, así que no se puede calcular
`target_variacion_matricula = (matrícula_t − matrícula_t−1)/matrícula_t−1` — **sin ≥2 ciclos no hay
objetivo supervisado**. Toca US-104 (Gold features/target), US-311 y US-313.

Hallazgo: [[14_Data_Sources/DS-01_Formato_911]] documenta que la serie del 911 existe desde 1990-91 y que
la SEP la publica **ya agregada** (SNIEE) a nivel `municipio × nivel`, multi-año. El "hueco" es de lo
descargado, no de lo publicado.

## Decisión del PO (DEC-007)
**Target híbrido de dos niveles:**
- **Primario:** target real multi-año a nivel `municipio × nivel` con la **serie SNIEE** (misma fuente
  DS-01, agregada — no una 9ª fuente); **features y driver dominante a nivel escuela** con el 911 2024-2025
  + los 6 drivers. Predice la variación municipal/nivel (validable con partición temporal) y conserva el
  desglose prescriptivo por escuela.
- **En paralelo:** perseguir el 2º ciclo crudo del 911 (2023-2024/2022-2023) para subir la granularidad
  del target a escuela si llega antes del gate S4.
- **Contingencia (disparo 2026-08-30):** índice compuesto de riesgo desde los 6 drivers, marcado
  `SIN_DATO_REAL`.

## Qué se hizo
- **`Risk_Register.md`** — RISK-007 `abierto` → **`mitigando`**, celda de mitigación reescrita con la
  estrategia doble + disparador y fecha.
- **`Decision_Log.md`** — **`DEC-007`** fija la definición del target y el fallback.
- **`DS-01_Formato_911.md`** — §2 serie SNIEE como distribución alterna; §9 dos ítems en la prueba de
  descarga (serie SNIEE + intento de 2º ciclo crudo) y trazas a DEC-007/RISK-007/US-104.
- **`Execution_Status.md`** — nota en US-104 y US-311 de que el target queda definido por DEC-007 (destraba
  la ambigüedad "ML sin objetivo").

## Corrección de gobernanza (revisión de Héctor en PR #56)
- **Colisión de ID DEC-005.** El target se registró primero como `DEC-005`, pero ese número ya designaba
  —sin registrar en el `Decision_Log`— la decisión del `indice_riesgo` del 13-14 ago (atajo `DEC-005/006`,
  referenciada en `publicar_gold.py`, `test_publicar_gold.py`, `Data_Model §4.5`, `Publicacion_Gold` y 4
  DevLogs). Se resolvió **registrando formalmente** ese hueco como **`DEC-005`** (contrato de schema de
  `gold.predicciones`) y **`DEC-006`** (umbral `indice_riesgo ≥ 0.6`), y **moviendo el target a `DEC-007`**
  en todo su rastro (Decision_Log, Risk_Register, DS-01, Execution_Status, `15_ML_Models/Target_Hibrido`
  —renombrado desde `Target_Hibrido_DEC005`—, `src/modelos/target_hibrido.py`, `generar_fixture_dim.py`,
  `tests/test_target_hibrido.py`, TEST-009 y los dos DevLogs del 19-ago). Los refs bare `DEC-005` del
  `indice_riesgo` quedan correctos sin tocarse. Se avisa a Héctor.
- **Matriz de trazabilidad de-duplicada.** REQ-002 y REQ-003 aparecían dos veces con contenido distinto por
  el `merge=union` de `.gitattributes` (union concatena filas; una tabla con una fila por REQ se corrompe).
  Se conservó la fila más completa de cada uno y se **retiró la matriz de `merge=union`** (queda solo para
  `_DevLog/_index.md`, que sí es log de solo-agregado).

## Verificación
- `generate` ✅ · `validate` (TEST-002) ✅ · `vault_lint` ✅.
- Baja real del riesgo (pendiente de Diana): cuando la serie SNIEE aterrice, US-104 calcula
  `target_variacion_matricula` no nulo para ≥1 `municipio × nivel` con ≥2 ciclos → US-311/US-313 dejan de
  estar bloqueadas por "sin objetivo".

## Siguiente acción (fuera de esta sesión)
Mensaje a **Diana** (dueña de DS-01): bajar la serie SNIEE municipio×nivel para las 4 entidades del scope
e intentar el 2º ciclo crudo del 911 con mapeo de esquema entre ciclos.
