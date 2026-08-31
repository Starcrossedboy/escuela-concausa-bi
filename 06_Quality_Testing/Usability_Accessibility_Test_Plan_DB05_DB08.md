---
id: DOC-USABILIDAD-DB0508
title: "Usability & Accessibility Test Plan — DB-05 / DB-08"
owner: "Monserrat Xcaret Miranda Olivas"
status: draft
traces_up: ["US-215b", "REQ-002"]
tags: [qa, usability, accessibility, db05, db08]
---

# Usability & Accessibility Test Plan — DB-05 / DB-08

> Guion de pruebas de usabilidad y accesibilidad para DB-05 (Análisis por driver, 6 tabs) y DB-08
> (Explorador del cubo), incluyendo el link cruzado entre ambos (US-214b).
> → [[06_Quality_Testing/_index]]

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

El checklist de accesibilidad de §3 se **adapta** de [[04_UX_Design/Accessibility]], no se copia
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
| 1.1 | Abrir DB-05, confirmar que carga en el tab D1 | El dashboard abre sin error, tab D1 activo por default | ✅ (2026-08-30) — confirmado, aunque hoy es el único tab visible por BUG-034; re-probar cuando se arregle | |
| 1.2 | Cambiar entre los 6 tabs (D1 → D6) | Cada tab muestra sus propios KPI tiles y tabla, filtrados por su `id_driver` | ❌ (2026-08-30) | BUG-034 |
| 1.3 | Aplicar los filtros globales (Ciclo, Entidad, Nivel) | Los tiles y la tabla recalculan según el filtro aplicado | ❌ (2026-08-30) — quitar un valor de Entidad y dar "Apply filters", o usar "Clear all", no cambia los datos visibles. Probado directo contra `/api/v1/chart/data` (sin navegador): el filtro sí funciona ahí, así que es un defecto de scope del filtro nativo, no del SQL | BUG-034 |
| 1.4 | En la tabla "Municipios · driver dominante y cobertura" de cualquier tab, localizar la columna del link | La columna se ve como texto de link (no HTML crudo), rotulada "Ver detalle del municipio →" | ✅ (2026-08-30) | |
| 1.5 | Hacer clic en el link de una fila | Abre DB-08 en pestaña nueva, con Municipio y Driver de esa fila pre-seleccionados | ✅ (2026-08-30) — confirmado con 2 filas distintas (municipio 09003→19039), el chart "Valor promedio del driver" de DB-08 cambió de valor entre una y otra (0.10 → 0.90), evidencia de que el filtro sí llegó aplicado | |
| 1.6 | Revisar legibilidad de números grandes en los KPI tiles | Formato consistente (separador de miles, decimales según `formato` de la métrica) | ✅ (2026-08-30) — contraste correcto en dark y light mode. Hallazgo aparte (no de formato numérico): el mensaje "sin datos" es inconsistente entre tiles y está en inglés — documentado como punto 5 de UX pendiente en `db08_explorador_cubo.yaml`, no se resuelve hoy (limitación de Superset) | |

### §2 — Usabilidad DB-08

| Caso | Pasos | Esperado | Resultado (✅/⚠️/❌/⏳) | Bug |
|---|---|---|---|---|
| 2.1 | Llegar a DB-08 directo (sin pasar por el link) | Los 5 filtros globales aparecen vacíos/default (Ciclo, Entidad, Nivel, Municipio, Driver) | ⏳ | |
| 2.2 | Llegar a DB-08 vía el link de DB-05 | Municipio y Driver llegan preseleccionados con el valor exacto de la fila de origen | ✅ (2026-08-30) — ver 1.5 | |
| 2.3 | Cambiar filas/columnas de la tabla dinámica libre | El pivote recalcula sin error, respeta `rowTotals`/`colTotals` en `false` | ⏳ | |
| 2.4 | Revisar la tabla de detalle sin agregar | Muestra `SIN_DATO` explícito donde no hay dato de un driver, nunca `0` silencioso (R2) | ⏳ | |

### §3 — Accesibilidad (DB-05 y DB-08)

Adaptado de [[04_UX_Design/Accessibility]] §Checklist, acotado a lo verificable en un dashboard de
Superset embebido (ver exclusiones en §Alcance).

| Caso | Pasos | Esperado | Resultado (✅/⚠️/❌/⏳) | Bug |
|---|---|---|---|---|
| 3.1 | Verificar contraste de texto (tiles, tablas, filtros) contra su fondo | Contraste AA (≥ 4.5:1) en el texto principal | ⏳ | |
| 3.2 | Navegar los controles propios de Superset (filtros nativos, tabs, orden de columnas de tabla) solo con teclado (Tab/Enter/flechas) | Todos los controles son alcanzables y operables sin mouse | ⏳ | |
| 3.3 | Verificar foco visible al tabular por los controles | El elemento con foco tiene un indicador visual claro | ⏳ | |

## Convención de resultados

✅ pasa · ⚠️ pasa con observación · ❌ falla (→ crear `BUG-###`) · ⏳ pendiente

## Hallazgos de alcance (huecos del proyecto, no se rellenan por cuenta propia)

- **Sin CI de accesibilidad real.** [[04_UX_Design/Accessibility]] declara "Lighthouse Accessibility
  ≥ 0.9 (bloqueante)", pero no hay ningún job de CI que lo ejecute — es aspiracional, no
  implementado. Este plan no puede heredar ese gate porque no existe.
- **Sin paleta de colores documentada.** No hay una paleta oficial del proyecto contra la cual
  verificar "colorblind-safe" (p. ej. distinguibilidad de series en gráficas de driver por tipo de
  daltonismo). Sin ese insumo, §3 no puede incluir un caso de prueba real para esto — se deja
  anotado aquí como hueco, no como caso ⏳.

## Cierre

- **Total ejecutados / pasados / fallidos:** 3 ejecutados (1.4, 1.5, 2.2) / 3 pasados / 0 fallidos —
  el resto queda `⏳ pendiente` para una siguiente pasada.
- **Bugs abiertos:** [[06_Quality_Testing/Bug_Register]]
