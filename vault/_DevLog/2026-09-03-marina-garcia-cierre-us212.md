---
project: "FARO"
date: "2026-09-03"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "continuación de la sesión de US-214a"
touches: ["US-212", "REQ-002", "REQ-003", "AC-002.4", "BUG-013", "BUG-031", "BUG-017", "ADR-007", "DEC-006"]
tags: [devlog, bi, dashboards, cierre, celula-2]
---

# DevLog — 2026-09-03 — Cierre de US-212 al 100 %

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/04_UX_Design/Cube_Specs_DB03_DB04]] §8.ter
· [[vault/_DevLog/2026-09-03-marina-garcia-us214a-drill-down|DevLog de US-214a, misma sesión]]

## Qué se hizo

US-212 estaba al **95 %** desde el 29-ago con un único bloqueo declarado: ratificar ADR-007 y que
la unidad del target llegara efectivamente al dato. Esta entrada verifica que el 5 % restante ya
está, y deja la evidencia asentada.

**No se cambió el estado en `Execution_Status.md`.** Esa ruta es `vault/12_Roadmap_Sprints/**`,
verde exclusivo del PM y ausente de `comunes`; el `check_ownership.py` reprobaría el PR. La
solicitud de cambiar `in_review` → `done` queda escrita en la matriz de trazabilidad.

## Lo que se verificó

### ADR-007 llegó al dato

| Paso | Dueño | Estado |
|---|---|---|
| 1 · Target a fracción en `features_escuela.sql` | C1 · Diana Alvarez | ✅ 31-ago |
| 2 · Rechazar `matricula_previa = 0` sin `NULLIF` silencioso | C1 · Diana Alvarez | ✅ 31-ago |
| 3 · Regenerar `gold.predicciones` | C3 · Héctor Morales | ✅ 2-3 sep |
| 4 · Reentrenar ML-01 | C3 · Héctor Morales | ✅ 2-3 sep |

Comprobado contra Postgres: `gold.predicciones.valor` en rango **−0.0437 … +0.0313** — es
fracción, no alumnos absolutos. `indice_riesgo` en **0.1637 … 0.5615**: deja de estar saturado,
que era exactamente el síntoma con el que la guarda de BUG-017 detenía la publicación, y con
razón.

### AC-002.4, el criterio que no se podía comprobar

- **55** escuelas con `cobertura_prediccion = OK`; **90** con `SIN_DATO` (los ciclos sin
  predicción — correcto, no un hueco)
- **24/24** charts de DB-03 y DB-04 con datos
- Los bloques de predicción y recomendación pueblan desde `gold.predicciones` real

Y lo importante: **reproducible solo con fixtures del repositorio**, que es lo que BUG-013 exigía
y no se podía. Las cifras coinciden con las que obtuvo **Héctor Morales por separado el mismo
día** (145 filas, 3 ciclos, 55 + 55), lo que descarta que sea un ambiente afortunado.

### KPI-02 por cinco caminos independientes

| Origen | KPI-02 |
|---|---|
| `gold.fact_escuela_ciclo` (verdad) | **−0.192 %** |
| `gold.cubo_matricula` → DB-01, DB-06 | **−0.192 %** |
| `gold.cubo_riesgo_territorial` → DB-02 | **−0.192 %** |
| `gold.cubo_escuela_360` → DB-03 | **−0.192 %** |
| `gold.cubo_comparador_municipio` → DB-04 | **−0.192 %** |

Sobre 32 312 / 32 374 alumnos: los mismos valores del reporte original de BUG-031.

### Regla `SIN_DATO`

D1 145/145 · D2 0/145 · D3 12/145 · D4 12/145 · D5 145/145 · D6 140/145, y **cero casos** en que
un driver marcado `SIN_DATO` traiga un valor.

## Dos registros que estaban desactualizados

- **BUG-031** decía `open` con un pendiente de C2 ("migrar los tres `metrics_*.yaml` y retirar
  `variacion_x_matricula`") que **ya estaba hecho desde el 31-ago**, y lo hizo **Luis Téllez**
  (`f013b20`, `b74a700`), no Manuel Serranía como decía la asignación. Verificado archivo por
  archivo y contra datos antes de marcarlo `fixed`.
- **BUG-013** seguía `parcial`, y su único pendiente era literalmente *"la dueña de DB-03 no
  puede verificar sus propios bloques ML (AC-002.4)"*. Eso es justo lo que se verificó hoy.
  Marcado `fixed`.

## Salvedad que se deja escrita

`en_riesgo = 0` en las 55 escuelas con predicción. **No es un defecto**: el riesgo máximo es
0.5615 contra el umbral 0.60 de DEC-006 — con datos de fixture nadie lo cruza. Con los datos
reales de Diana el resultado puede ser otro, y conviene revisarlo antes de la demo del 9-sep.
Se prefiere dejarlo dicho a que aparezca en vivo.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `vault/06_Quality_Testing/Bug_Register.md` (BUG-031 y BUG-013),
  `vault/04_UX_Design/Cube_Specs_DB03_DB04.md` (§8.ter), `vault/02_Requirements/Traceability_Matrix.md`,
  este DevLog, `vault/_DevLog/_index.md`
- **Fuera de alcance, NO editado:** `vault/12_Roadmap_Sprints/Execution_Status.md` y el propio
  plan de sprint. Ambos son verde exclusivo del PM y no están en `comunes`; el cambio de estado
  se solicita, no se ejecuta.
- **Decisiones autónomas del agente:** verificar los dos registros contra el código y contra
  Postgres antes de tocarles el estado, en vez de darlos por buenos.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Sin archivos fuera de alcance (`check_ownership.py` en verde)
- [x] `vault_lint.py` ✅ · `ruff` ✅ · suite completa en verde
- [x] Trazabilidad actualizada con la solicitud explícita al PM

## Bloqueantes

- **Edgar Coronel (PM):** cambiar `US-212` de `in_review` a `done` en `Execution_Status.md` y
  actualizar la fila de la tabla de seguimiento de mi plan de sprint. Ninguna de las dos rutas
  está en mi alcance.

## Próximos pasos

- US-215a: bloqueada por alcance (`vault/06_Quality_Testing/` sin dueño en `ownership.yml`).
- US-207: pendiente de acordar alcance con el PM.
