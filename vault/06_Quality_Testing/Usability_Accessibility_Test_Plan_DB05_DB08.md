---
id: DOC-USABILIDAD-DB0508
title: "Usability & Accessibility Test Plan — DB-05 / DB-08"
owner: "Monserrat Xcaret Miranda Olivas"
status: approved
traces_up: ["US-215b", "REQ-002"]
traces_down: ["BUG-038", "BUG-051"]
last_reviewed: "2026-09-04"
tags: [qa, usability, accessibility, db05, db08]
---

# Usability & Accessibility Test Plan — DB-05 / DB-08

> Guion de pruebas de usabilidad y accesibilidad para DB-05 (Análisis por driver, 6 tabs) y DB-08
> (Explorador del cubo), incluyendo el link cruzado entre ambos (US-214b).
> → [[vault/06_Quality_Testing/_index]]

## Alcance

**Cubre:**
- DB-05 · Análisis por driver — los 6 tabs (D1-D6) y su tabla "Municipios · driver dominante y
  cobertura", incluyendo la columna `link_db08` nueva (US-214b).
- DB-08 · Explorador del cubo — filtros globales, tabla dinámica libre y tabla de detalle.
- El viaje completo DB-05 → DB-08 vía el link (RISON `native_filters`, US-214b).

**No cubre — corresponde a otra historia:**
- El shell de FARO Web (React/Streamlit, US-206/US-207, dueño Manuel Serranía): ARIA de sus
  componentes propios, `prefers-reduced-motion`, layout responsivo del shell.
- El código fuente interno de Superset (controles nativos, dropdowns de filtro): se prueba su
  comportamiento visible, no se audita su implementación — es un tercero, no algo que el equipo
  pueda corregir.

El checklist de accesibilidad de §3 se **adapta** de [[vault/04_UX_Design/Accessibility]], no se copia
íntegro: de sus 6 ítems, se excluyen "Roles/labels ARIA en controles" (fuera de alcance — controles
de Superset, no propios) y "Respeta `prefers-reduced-motion`" (shell de FARO Web).

## Matriz de alcance

| Dashboard | Navegador | Responsable |
|---|---|---|
| DB-05 · Análisis por driver (6 tabs) | Chrome | Monserrat Xcaret Miranda Olivas |
| DB-08 · Explorador del cubo | Chrome | Monserrat Xcaret Miranda Olivas |

## Guion por sección

### §1 — Usabilidad DB-05

| Caso | Pasos | Esperado | Resultado (✅/⚠️/❌/⏳) | Bug |
|---|---|---|---|---|
| 1.1 | Abrir DB-05, confirmar que carga en el tab D1 | El dashboard abre sin error, tab D1 activo por default | ✅ (2026-09-04) — re-probado tras el fix de BUG-038: abre en D1 con `aria-selected: true` y **los 6 tabs visibles** en la barra. La salvedad de 2026-08-30 ("hoy es el único tab visible") queda resuelta | |
| 1.2 | Cambiar entre los 6 tabs (D1 → D6) | Cada tab muestra sus propios KPI tiles y tabla, filtrados por su `id_driver` | ✅ (2026-09-04) — **antes ❌ por BUG-038**. Verificado en navegador real contra Superset 6.1.0: los 6 tabs se dibujan y al cambiar a D4 su panel queda `aria-hidden: false` con **6 charts** y su propia nota ("CEMABE (DS-03) · medido a nivel escuela"). Los valores son propios de cada tab, no heredados: D1 → 52.7 % / 18 escuelas; D4 → 30.9 % / 17. Antes del fix D2-D6 eran inalcanzables | BUG-038 ✅ |
| 1.3 | Aplicar los filtros globales (Ciclo, Entidad, Nivel) | Los tiles y la tabla recalculan según el filtro aplicado | ✅ (2026-09-04) — **antes ❌ por BUG-038**. Con `nombre_entidad = 'Jalisco'` el panel muestra el valor y los charts **sí recalculan**: KPI-07 pasa de 52.7 % a 0.0 % y "Escuelas por driver dominante" de 18 a 0. **Contrastado contra la base**, no sólo contra la pantalla: `gold.cubo_driver` da para Jalisco/D1/2024-2025 `escuelas_driver = 0` sobre `total_escuelas = 7`, y el cuarto tile muestra exactamente 7. Sin filtro, los 18 del tablero son la suma real (0+0+10+8) de las 4 entidades | BUG-038 ✅ |
| 1.4 | En la tabla "Municipios · driver dominante y cobertura" de cualquier tab, localizar la columna del link | La columna se ve como texto de link (no HTML crudo), rotulada "Ver detalle del municipio →" | ✅ (2026-08-30) | |
| 1.5 | Hacer clic en el link de una fila | Abre DB-08 en pestaña nueva, con Municipio y Driver de esa fila pre-seleccionados | ✅ (2026-08-30) — confirmado con 2 filas distintas (municipio 09003→19039), el chart "Valor promedio del driver" de DB-08 cambió de valor entre una y otra (0.10 → 0.90), evidencia de que el filtro sí llegó aplicado | |
| 1.6 | Revisar legibilidad de números grandes en los KPI tiles | Formato consistente (separador de miles, decimales según `formato` de la métrica) | ✅ (2026-08-30) — contraste correcto en dark y light mode. Hallazgo aparte (no de formato numérico): el mensaje "sin datos" es inconsistente entre tiles y está en inglés — documentado como punto 5 de UX pendiente en `db08_explorador_cubo.yaml`, no se resuelve hoy (limitación de Superset) | |

### §2 — Usabilidad DB-08

| Caso | Pasos | Esperado | Resultado (✅/⚠️/❌/⏳) | Bug |
|---|---|---|---|---|
| 2.1 | Llegar a DB-08 directo (sin pasar por el link) | **Ciclo llega preseleccionado en `2024-2025`** (comportamiento correcto desde BUG-047); Entidad, Nivel, Municipio y Driver llegan vacíos | ✅ (2026-09-04) — verificado por API sobre `native_filter_configuration`: `-0` Ciclo → `defaultDataMask` con `['2024-2025']`; `-1` Entidad, `-2` Nivel, `-3` Municipio y `-4` Driver sin `defaultDataMask`. **Esperado reescrito hoy**: decía "los 5 aparecen vacíos/default", redacción anterior a BUG-047 que habría marcado falla falsa | |
| 2.2 | Llegar a DB-08 vía el link de DB-05 | Municipio y Driver llegan preseleccionados con el valor exacto de la fila de origen | ✅ (2026-08-30) — ver 1.5 · **Regresión revisada (2026-09-04)**: los IDs de filtro se generan **por posición**, y BUG-047 añadió `valor_por_defecto` a `id_ciclo`. Contrastado el RISON de `link_db08` contra el tablero desplegado: sigue apuntando a `-3` (`cve_mun`) y `-4` (`id_driver`), que son los índices reales. Sin regresión | |
| 2.3 | Cambiar filas/columnas de la tabla dinámica libre | El pivote recalcula sin error, respeta `rowTotals`/`colTotals` en `false` | ✅ (2026-09-04) — verificado por API sobre el chart 95: `viz_type: pivot_table_v2`, `groupbyRows` `[nombre_entidad, nombre_municipio, nivel]`, `groupbyColumns` `[id_driver, nombre_driver]`, `rowTotals: False`, `colTotals: False`; `/api/v1/chart/data` responde **180 filas, `status: ok`** | |
| 2.4 | Revisar la tabla de detalle sin agregar | Muestra `SIN_DATO` explícito donde no hay dato de un driver, nunca `0` silencioso (R2) | ✅ (2026-09-04) — verificado **en datos** sobre `gold.cubo_pivot`: **309 filas** marcadas `SIN_DATO` (D3 12, D4 12, D5 145, D6 140) y **ninguna** trae valor. Prueba discriminante: conviven con **60 ceros legítimos** en filas `OK` (D1 15, D2 15, D3 2, D4 43, D6 2) — el cero real existe y no se confunde con el hueco | |

### §3 — Accesibilidad (DB-05 y DB-08)

Adaptado de [[vault/04_UX_Design/Accessibility]] §Checklist, acotado a lo verificable en un dashboard de
Superset embebido (ver exclusiones en §Alcance).

| Caso | Pasos | Esperado | Resultado (✅/⚠️/❌/⏳) | Bug |
|---|---|---|---|---|
| 3.1 | Verificar contraste de texto (tiles, tablas, filtros) contra su fondo | Contraste AA (≥ 4.5:1) en el texto principal | ⚠️ (2026-09-04, **oscuro y claro**) — ratio calculado sobre el color y el fondo **efectivos** de cada nodo de texto visible. **Oscuro: 30/32 cumplen** · **Claro: 31/34 cumplen**. El único fallo que es contenido del tablero —y no chrome de Superset— es la **etiqueta del tab activo**, y **está peor en claro que en oscuro: 3.55:1 vs 4.07:1**, ambos bajo el mínimo de 4.5:1 para texto de 14 px. Los demás fallos son del chrome, explícitamente fuera de alcance: `Edit dashboard` (3.41 oscuro / 3.07 claro) y `Published` (2.16, sólo claro). Ver [[vault/06_Quality_Testing/Bug_Register]] BUG-051 | BUG-051 |
| 3.2 | Navegar los controles propios de Superset (filtros nativos, tabs, orden de columnas de tabla) solo con teclado (Tab/Enter/flechas) | Todos los controles son alcanzables y operables sin mouse | ✅ (2026-09-04) — **alcanzabilidad**, medida: 48 elementos enfocables, los **6/6 tabs** y los **3/3 filtros globales** en el orden de tabulación, y cada tab se anuncia como "Tab N of 6" (posición expuesta a lector de pantalla). **Activación, verificada a mano por Monserrat Xcaret Miranda Olivas** en Chrome: `Tab` hasta la pestaña + `Enter` **sí cambia de tab**. La comprobación humana era necesaria: el navegador automatizado no entregaba ni `Enter` ni clic a los tabs de React (aunque un `.click()` del DOM sí funcionaba), así que la herramienta habría reportado un falso negativo — **era artefacto de medición, no defecto**. Salvedad real: las **flechas ← → no mueven entre tabs**, Superset no implementa el patrón ARIA completo de `tablist`; no bloquea la operación porque `Tab`+`Enter` cubre el recorrido, y es su componente, no del equipo | |
| 3.3 | Verificar foco visible al tabular por los controles | El elemento con foco tiene un indicador visual claro | ✅ (2026-09-04) — tabulando con `Tab` real, el elemento activo cumple `:focus-visible` y pinta un anillo `box-shadow: rgb(37,128,155) 0 0 0 2px`. `outline-style` es `none`: el indicador es la sombra, no el outline — quien audite mirando sólo `outline` concluiría falsamente que no hay foco visible. Un `.focus()` programático **no** dispara `:focus-visible` y no sirve para verificar este caso | |

## Convención de resultados

✅ pasa · ⚠️ pasa con observación · ❌ falla (→ crear `BUG-###`) · ⏳ pendiente

## Hallazgos de alcance (huecos del proyecto, no se rellenan por cuenta propia)

- **Sin CI de accesibilidad real.** [[vault/04_UX_Design/Accessibility]] declara "Lighthouse Accessibility
  ≥ 0.9 (bloqueante)", pero no hay ningún job de CI que lo ejecute — es aspiracional, no
  implementado. Este plan no puede heredar ese gate porque no existe.
- **Sin paleta de colores documentada.** No hay una paleta oficial del proyecto contra la cual
  verificar "colorblind-safe" (p. ej. distinguibilidad de series en gráficas de driver por tipo de
  daltonismo). Sin ese insumo, §3 no puede incluir un caso de prueba real para esto — se deja
  anotado aquí como hueco, no como caso ⏳.

## Cierre

**Segunda pasada — 2026-09-04.** El ambiente local se levantó desde cero siguiendo
[[vault/00_Start_Here/Runbook_Ambiente_Local]] y todas sus cifras de control salieron exactas
(`fact_escuela_ciclo` 145 · 55 predicciones · 8/9 cubos · 103 charts / 9 tableros ·
`matricula_total` 11 828), así que lo verificado aquí corre sobre un Gold íntegro, no degradado.

| | Casos |
|---|---|
| **Ejecutados** | **13 de 13** |
| ✅ pasan | **12** — 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 3.2, 3.3 |
| ⚠️ pasan con observación | 1 — 3.1 (contraste del tab activo, → BUG-051) |
| ❌ fallan | **0** |

- **1.2 y 1.3 pasaron de ❌ a ✅**: eran los dos síntomas de **BUG-038**, corregido en esta misma
  sesión (`_layout_tabs()` armaba `ROOT_ID` como `TABS` y colgaba un `GRID` entre cada `TAB` y sus
  `ROW`; ambos defectos había que arreglarlos juntos). Verificado en navegador real, no sólo por API
  — que es justo lo que hacía falta: los tests unitarios estaban en verde mientras el tablero
  estaba roto, porque **codificaban la estructura defectuosa como la esperada**.
- **El caso 2.1 se reescribió antes de ejecutarlo.** Su esperado era anterior a BUG-047 y habría
  marcado una falla falsa: el Ciclo hoy llega preseleccionado a propósito.
- **§3.2 se cerró con comprobación humana, y hacía falta.** El navegador automatizado no entregaba
  `Enter` ni clic a los tabs de React —aunque sí movía el foco— y habría reportado un **falso
  negativo**. Se dejó sin marcar hasta que la autora lo verificó a mano en Chrome: `Tab` + `Enter`
  cambia de pestaña. Era artefacto de medición, no defecto. Queda como salvedad que las flechas
  ← → no navegan entre tabs (patrón ARIA incompleto de Superset, no bloquea la operación).
- **§3.1 se midió en los dos temas.** El único fallo que es contenido del tablero —la
  etiqueta del tab activo— **está peor en claro (3.55:1) que en oscuro (4.07:1)**, así que
  BUG-051 no se resuelve fijando un tema por defecto.

- **Bugs abiertos:** [[vault/06_Quality_Testing/Bug_Register]] — **BUG-051** (contraste del tab
  activo) nace de esta pasada. **BUG-038** queda listo para cerrarse con esta evidencia.
