---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión única: respuesta a revisión de PR #190 — tableros DB-07/DB-10 y correcciones al manual"
touches: ["US-222", "US-223", "US-224", "REQ-002", "BUG-029"]
tags: [devlog]
---

# DevLog — 2026-09-02 — Tableros DB-07/DB-10 y correcciones al manual (respuesta a revisión)

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué pedí

Tras el merge de PR #190, recibí una revisión (vía Edgar Coronel) que señalaba tres puntos:
(P1) faltaba la definición declarativa del tablero de DB-07 y DB-10 en
`superset/dashboards/*.yaml` — la capa semántica (SQL + métricas) estaba completa, pero sin eso
Superset no tiene charts que abrir aunque hubiera datos; (P2) dos imprecisiones en el manual de
usuario (sobredeclaraba la validación de DB-01/DB-02 y tenía una frase vencida sobre ML-01); (P3)
una cadena de dependencias de Bronze/Célula 1 para las 8 capturas restantes, fuera de mi control.
Pedí verificar cada punto contra el repo antes de actuar, y resolver lo que sí depende de mí.

## Qué hizo la IA

- Verificó P1 con `ls superset/dashboards/`: en efecto solo existían 8 de 10 (faltaban
  `db07_*` y `db10_*`).
- Verificó P2a leyendo el DevLog completo de Luis Téllez
  (`2026-09-01-luis-tellez-superset-validacion-local.md`): confirma textualmente "Los números NO
  se validan aquí" y dependencia del recálculo del Carril A — la tabla del manual sí sobredeclaraba.
- Verificó P2b: `US-311` está `in_progress` desde 2026-08-08 con PR #28 mergeado (MAE 0.0141 /
  RMSE 0.0177) — la frase "llega en Sprint 4" del manual quedó vencida (estamos en Sprint 6).
- Escribió `superset/dashboards/db07_calidad_cobertura.yaml` (7 charts: 4 tiles KPI-05/06 +
  mapa de vacíos `deck_polygon` + desglose por driver + tabla detallada) y
  `superset/dashboards/db10_monitor_pipeline.yaml` (5 charts: 4 tiles + tabla de las 8 fuentes),
  siguiendo el mismo esquema que los 8 tableros ya existentes — leyó `_params_chart()` en
  `sync_semantic_layer.py` para no inventar claves que el sync no reconoce, y usó únicamente
  columnas/métricas que ya existen en `db07_cubo_completitud.sql`, `db07_mapa_vacios.sql`,
  `db10_cubo_pipeline.sql`, `metrics_db07.yaml` y `metrics_db10.yaml`.
- Corrigió el manual: la tabla de "Estado de este manual" ahora distingue estructura vs. números
  para DB-01/DB-02, y las secciones de DB-07/DB-10 ya mencionan la definición de tablero nueva.
  Actualizó la frase de ML-01 en DB-03 con el estado real (`US-311`, PR #28, métricas reales).

## Qué revisé yo

- Validé sintaxis y campos obligatorios de ambos YAML con `yaml.safe_load` + aserciones por chart
  antes de darlos por buenos.
- No intenté forzar un `sync` en vivo contra Superset: `gold.cubo_completitud`/`gold.cubo_pipeline`
  no están materializados en este ambiente (mismo bloqueo de Bronze de siempre) y BUG-029
  (reservado a mí, `Bug_Register.md`) documenta que un solo dataset roto aborta la corrida completa
  — probarlo ahora habría sido ruido, no señal.
- Corrí la suite completa (774 passed, 5 skipped) y `vault_lint.py` (limpio) tras los cambios.
- No toqué nada de P3 (Bronze/Diana, procedimiento de Luis, `kpi_01_matricula_total.sql` de
  Manuel) — son dependencias reales de otras personas, documentadas, no mías.

## Qué falta / bloqueos

- **P1 y P2 quedan cerrados con este commit.** Con esto, US-222 y US-223 tienen su tablero
  definido, no solo la capa semántica — falta que Bronze se cargue para que
  `sync_semantic_layer.py` los registre con datos reales.
- **P3 sigue bloqueado, no es mío:** Diana Álvarez (C1) — cargar Bronze + `dbt run` de Gold
  completo, en el orden P-03 (geometrías antes de dbt). Luis Téllez (C5) — pedirle el
  procedimiento/acceso al stack donde ya validó DB-01/DB-02. Manuel Serranía (C2 TL) — decisión
  sobre el huérfano `kpi_01_matricula_total.sql`, no lo toco sin su ratificación.
- Las 10 capturas de US-224 siguen pendientes de ese mismo desbloqueo.

## IDs tocados

US-222, US-223, US-224, REQ-002, BUG-029
