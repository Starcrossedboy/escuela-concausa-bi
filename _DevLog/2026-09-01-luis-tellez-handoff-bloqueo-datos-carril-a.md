---
project: "FARO"
date: "2026-09-01"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — desbloqueo de Carril A: handoff de qué falta para el recálculo de producción-local (P-01/P-02), sin inventar URLs"
touches: ["RPT-DATOS-BLOQUEO-P01-2026-09-01", "DS-02", "DS-03", "DS-06", "DS-08"]
tags: [devlog, data-sources, blocker, carril-a, handoff, pm, report]
---

# DevLog — 2026-09-01 — Handoff: qué falta para desbloquear Carril A (P-01/P-02)

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Cerrado ya el Carril B (8/8, PRs #172–#182) y la consolidación de Carril C (6 costuras
confirmadas en runtime + BUG-035 → PR #183 mergeado), toca el **Carril A**. De sus 10 renglones,
**7 están cerrados en código** (transformación, `matricula_ciclo_anterior`, target en fracción
ADR-007, argmax invertido P-05, D2 como tasa P-10, `dim_municipio` universo INEGI P-03, KPI-02
razón de sumas) y el **renglón 3** (auditoría de los 56 tests `dbt/tests/`) quedó **limpio** esta
sesión (ningún test codifica el defecto; los dos que tocan esas áreas son guardas que lo cazan).

Los **renglones 8, 9 y 10 están bloqueados por una sola causa**: faltan **URLs de descarga reales**
que **no se pueden inventar** (CLAUDE.md "Nunca inventes rutas de fuentes de datos"; Carril A §1
REGLA PRIME "ante cualquier duda, pregunta"). El renglón 10 (recálculo `publicar_gold --desde-gold`)
cuelga de P-01 (8 fuentes reales), que cuelga de P-02 (CEMABE), que cuelga de esas URLs.

## Decisión (con Luis)

Ante el bloqueo, elegimos **documentar qué falta** (Carril A §10: "tú dejas escrito qué haría
falta"), **no inventar dato**. Y — dado que B y C ya cerraron y con ellos la razón de §3 para no
tocar el vault (colisiones entre carriles en paralelo) — se **sigue el vault** para este entregable
(DevLog + índice + IDs), como en B y C.

## Qué hice

- Redacté el handoff `13_Reports/Datos_Bloqueo_P01_Carril_A_2026-09-01.md`
  (id `RPT-DATOS-BLOQUEO-P01-2026-09-01`): estado real de las 8 fuentes / 9 tablas Bronze
  (extractor · URL · cargador real · qué falta · dueño), la regla **"las 8 suben juntas o ninguna"**,
  la cadena **8→9→10**, la ruta de desbloqueo ordenada y una **nota de método** que separa lo
  **leído** de lo **deducido** de lo que **dice un documento** (posible desactualización).
- Lo di de alta en `13_Reports/_index.md`.

**Cero cambios de código.** No toqué `dbt/**`, `src/ingesta/**`, `src/modelos/**` ni fixtures: no
hay nada que codificar hasta que existan las URLs.

## Lo que bloquea, por dueño (accionable)

- **Diana** — URL de **DS-02 Catálogo CCT** (no existe extractor) + confirmar corrida real de DS-01.
- **Deni** — URL de **DS-03 CEMABE** + **muestra del CSV** para escribir el parser (renglón 8).
- **Emilio** — URL de **DS-08 CONAPO** y aclarar **DS-06 CONAGUA** (la ficha dice `PENDIENTE` pero
  Carril A §9 afirma que el extractor funciona; manda el código, se actualiza la ficha).

DS-04 (SESNSP) y DS-05 (SINAICA) ya tienen URL verificada y extractor intocable (§9); DS-07 (CONEVAL)
se resolvió en #151. A esas tres **podría** faltarles el cargador real a Bronze (solo existe el de
DS-01) — marcado como "por confirmar", es trabajo de Carril A que **solo aplica con la URL en mano**.

## Validación

- `vault_lint.py .` → limpio (los 4 wikilinks del reporte resuelven: `14_Data_Sources/_index`,
  `14_Data_Sources/DS-03_CEMABE`, `13_Reports/US_Pendientes_Cierre_2026-08-30`,
  `12_Roadmap_Sprints/Execution_Status`).
- Sin código tocado ⇒ suite y `ruff` sin cambio respecto a `main` (669 passed, ruff 0 del corte previo).

## Territorio / gobernanza

Entregable **documental** de Carril A; rama `carril-a/handoff-bloqueo-datos`, **PR para
@edgarcoroneln** (no mergeo). No promoví nada a producción; no inventé ninguna URL.
