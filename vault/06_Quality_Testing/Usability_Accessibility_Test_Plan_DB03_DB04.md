---
id: DOC-USABILIDAD-DB0304
title: "Usability & Accessibility Test Plan — DB-03 / DB-04"
owner: "Marina García del Buey"
status: draft
traces_up: ["US-215a", "REQ-002"]
tags: [qa, usability, accessibility, db03, db04]
---

# Usability & Accessibility Test Plan — DB-03 / DB-04

> Guion de pruebas de usabilidad y accesibilidad para **DB-03 (Ficha de escuela)** y
> **DB-04 (Comparador de municipios)**, incluyendo los filtros globales y el drill-down
> cruzado entre ambos (US-214a).
> → [[vault/06_Quality_Testing/_index]] · Contrato: [[vault/04_UX_Design/Cube_Specs_DB03_DB04]]

## Alcance

Calca el formato del plan de Monserrat Miranda para DB-05/DB-08
([[vault/06_Quality_Testing/Usability_Accessibility_Test_Plan_DB05_DB08]]), para que los
cuatro tableros de la célula se lean igual.

**Adapta** —no copia íntegro— el checklist de [[vault/04_UX_Design/Accessibility]], acotado
a lo verificable en un dashboard de Superset embebido. Quedan **excluidos explícitamente**:

- ARIA de componentes propios de FARO Web (es US-206/US-207, de la capa Streamlit)
- `prefers-reduced-motion` (mismo motivo)
- Lighthouse automatizado: **no existe ese gate en el proyecto**, pese a que
  `Accessibility.md` lo declara como bloqueante. Ver §Hallazgos de alcance.

## Matriz de alcance

| Dashboard | Navegador | Responsable |
|---|---|---|
| DB-03 · Ficha de escuela | Chrome | Marina García del Buey |
| DB-04 · Comparador de municipios | Chrome | Marina García del Buey |

## Guion por sección

### §1 — Usabilidad DB-03

| Caso | Pasos | Esperado | Resultado | Bug |
|---|---|---|---|---|
| 1.1 | Abrir DB-03 sin tocar nada | Carga sin error, con el **ciclo 2024-2025 ya preseleccionado** en la barra de filtros | ✅ (2026-09-04) — verificado por API: `defaultDataMask` persistido en `NATIVE_FILTER-US203-1` con `val: ['2024-2025']` | |
| 1.2 | Leer la tarjeta `KPI-15 · Matrícula de la escuela` recién abierto | La cifra corresponde **al ciclo**, no a la suma de todos los ciclos del cubo | ✅ (2026-09-04) — verificado contra `/api/v1/chart/data`: sin filtro devuelve 32 312, con el ciclo devuelve **11 828**. El defecto inflaba 2.73× | |
| 1.3 | Aplicar los filtros globales (Ciclo, Entidad, Nivel) | Las tarjetas y tablas recalculan según el filtro | ⏳ pendiente en navegador | |
| 1.4 | Filtrar por una escuela concreta con el filtro `Escuela (CCT)` | El tablero se vuelve la ficha de esa escuela: perfil, drivers, predicción y recomendación de ese CCT (AC-002.4) | ⏳ pendiente en navegador | |
| 1.5 | Revisar la tabla `KPI-16 · Drivers de la escuela y su cobertura` | Donde no hay dato de un driver muestra `SIN_DATO` explícito, **nunca `0`** (regla R2) | ✅ (2026-09-04) — verificado en datos: D1 145/145 `SIN_DATO`, D5 145/145, D6 140/145, y **cero casos** de driver marcado `SIN_DATO` que traiga valor | |
| 1.6 | En `Perfil del plantel`, localizar la columna del link a DB-04 | Se ve como texto de link (no HTML crudo), rotulado "Comparar su municipio →" | ⏳ pendiente en navegador | |
| 1.7 | Hacer clic en ese link | Abre DB-04 en pestaña nueva con Ciclo y Municipio de esa fila preseleccionados | ✅ estructura (2026-09-04) — RISON decodificado con `prison` y contrastado contra el tablero desplegado: `NATIVE_FILTER-US203-0`→`id_ciclo`, `-4`→`cve_mun`, ambos correctos. ⏳ falta confirmar visualmente el salto | |
| 1.8 | Leer `KPI-17 · Índice de riesgo` | Muestra el índice, y el subheader explica el umbral 0.60 de DEC-006 | ⚠️ (2026-09-04) — el valor se muestra bien, pero **ninguna escuela cruza 0.60** (máx. 0.562). No es defecto del tablero: ver [[vault/04_UX_Design/Cube_Specs_DB03_DB04]] §8.quinquies. Decisión de narrativa pendiente de mesa | |

### §2 — Usabilidad DB-04

| Caso | Pasos | Esperado | Resultado | Bug |
|---|---|---|---|---|
| 2.1 | Abrir DB-04 sin tocar nada | Carga con el ciclo 2024-2025 preseleccionado | ✅ (2026-09-04) — `defaultDataMask` en `NATIVE_FILTER-US203-0` | |
| 2.2 | Leer `KPI-01 · Matrícula de los municipios` recién abierto | Cifra del ciclo, no la suma | ✅ (2026-09-04) — 11 828 con filtro contra 32 312 sin él | |
| 2.3 | Seleccionar 2-3 municipios en `Municipios a comparar` | La comparativa y los seis small-multiples de driver recalculan solo con esos municipios | ⏳ pendiente en navegador | |
| 2.4 | Revisar `KPI-02 · Variación de matrícula` | Razón de sumas, coherente con el hecho | ✅ (2026-09-04) — **−0.496 %** en el ciclo, idéntico por los cinco caminos (hecho + 4 cubos). Ver §8.ter.3 del contrato | |
| 2.5 | Revisar los seis paneles de driver (D1…D6) | Cada promedio divide entre `escuelas_con_d#`, y los `SIN_DATO` no aparecen como cero | ⏳ pendiente en navegador | |
| 2.6 | En `Comparativa de municipios`, hacer clic en el link a DB-03 | Abre DB-03 con Ciclo y Municipio preseleccionados, y `cct` **libre** (para elegir escuela) | ✅ estructura (2026-09-04) — `NATIVE_FILTER-US203-1`→`id_ciclo`, `-4`→`cve_mun`; `cct` (índice 0) deliberadamente sin fijar. ⏳ falta confirmar visualmente | |
| 2.7 | Revisar `KPI-14 · Contexto socioeconómico` | Muestra población, pobreza y rezago del municipio | ⚠️ (2026-09-04) — en ambiente local sale vacío porque **CONEVAL no es ingerible desde los fixtures del repo** (hallazgo abierto de C1). En producción sí hay dato: re-probar ahí | |

### §3 — Accesibilidad (DB-03 y DB-04)

Requiere navegador; ninguno automatizable con lo que hay hoy en el proyecto.

| Caso | Pasos | Esperado | Resultado | Bug |
|---|---|---|---|---|
| 3.1 | Verificar contraste de texto (tarjetas, tablas, filtros) contra su fondo, en claro y oscuro | Contraste AA (≥ 4.5:1) en el texto principal | ⏳ | |
| 3.2 | Recorrer los controles de Superset (filtros nativos, orden de columnas, links de drill-down) solo con teclado | Todos alcanzables y operables sin mouse | ⏳ | |
| 3.3 | Verificar foco visible al tabular | El elemento con foco tiene indicador visual claro | ⏳ | |
| 3.4 | Activar el link de drill-down con **Enter** (no con clic) | Navega igual que con el mouse | ⏳ — relevante porque el link es un `<a href>` renderizado con `allow_render_html`, no un control nativo de Superset | |
| 3.5 | Revisar que `SIN_DATO` se distinga por texto y no solo por color | Un usuario con daltonismo distingue el hueco del cero | ⏳ | |

## Convención de resultados

`✅` verificado · `⚠️` verificado con salvedad · `❌` falla, con bug registrado · `⏳` pendiente

## Hallazgos de alcance (huecos del proyecto, no se rellenan por cuenta propia)

1. **No hay CI de accesibilidad.** [[vault/04_UX_Design/Accessibility]] declara
   *"verificados en CI (Lighthouse a11y)"* y *"Lighthouse Accessibility ≥ 0.9
   (bloqueante)"*. No existe ninguna referencia a Lighthouse en `.github/` ni en
   `vault/08_CICD_DevOps/`. Todo el §3 se verifica a mano. Mismo hueco que documentó
   Monserrat en US-215b: es del proyecto, no de esta historia.

2. **No hay paleta de colores documentada.** [[vault/04_UX_Design/UX_Guidelines]] está en
   `status: draft` con las tablas de tokens y componentes **vacías**, pese a llevar
   `source_of_truth: true`. Sin paleta declarada, el §3.1 se verifica contra lo que
   Superset trae por default, no contra un estándar del proyecto.

3. **El §3 no se puede cerrar sin sesión de navegador.** Se documenta como pendiente en
   vez de declararlo verificado: un plan de accesibilidad firmado sin haber tabulado por
   los controles no vale nada.

## Cierre

Los casos con evidencia de datos o de API se verificaron el **2026-09-04** y quedan
cerrados. Los que exigen navegador quedan `⏳` para una segunda pasada, con la lista
explícita de arriba. No se marca ninguno como verificado sin haberlo corrido.
