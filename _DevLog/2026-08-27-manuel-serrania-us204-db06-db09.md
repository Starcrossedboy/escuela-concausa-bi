---
project: "FARO"
date: "2026-08-27"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
session_duration: "construcción + validación en vivo de US-204: contrato Cube_Specs DB-06/DB-09,
 3 datasets virtuales, métricas YAML, tableros declarativos, mock con grano dual, 50 pruebas y
 sync end-to-end con AC-002.2"
touches: ["US-204", "REQ-002", "DOC-CUBESPEC-DB0609", "KPI-01", "KPI-02", "KPI-03", "KPI-04", "KPI-05", "KPI-07", "KPI-11", "KPI-12", "DEC-010", "DEC-009", "DEC-008", "MOC-04", "MOC-DEVLOG"]
tags: [devlog, bi, superset, capa-semantica, predicciones, recomendaciones, celula-2]
---

# DevLog — 2026-08-27 — US-204: DB-06 Predicciones y DB-09 Recomendaciones prescriptivas

→ [[_DevLog/_index|Volver al índice]] · [[04_UX_Design/Cube_Specs_DB06_DB09]] · [[04_UX_Design/Screen_Specs]] · [[03_Architecture/Data_Model]]

## Contexto
US-204 cierra el diferenciador prescriptivo del proyecto: el tablero que dice **qué intervención
le toca a cada escuela** (DB-09) y el que muestra **hacia dónde va la matrícula** (DB-06). Se
construye sobre la convención de capa semántica de US-202/US-211a/US-211b y consume las salidas
de ML-01 (`gold.predicciones`, **grano dual DEC-010**) y ML-02 (`gold.recomendaciones`).

Estado de las dependencias al 27-ago: C3 aún publica predicciones/recomendaciones en
**MOCK-US203** (job US-313 en progreso), y los cubos físicos `gold.cubo_matricula` /
`gold.cubo_recomendaciones` de C1 (US-113) están en revisión → los datasets son **SQL virtual
autocontenido** que sirven de dataset hoy y de SQL de referencia mañana (mismo trato que US-211a):
cuando el cubo físico exista, el SQL del dataset se reduce a `SELECT * FROM gold.<cubo>`.

## Qué se hizo

### Contrato (`04_UX_Design/Cube_Specs_DB06_DB09.md`, DOC-CUBESPEC-DB0609)
- Granos: `db06_cubo_predicciones` = `cve_mun × nivel × id_ciclo` (espejo de `gold.cubo_matricula`, DEC-009);
  `db06_predicciones_escuela` y `db09_cubo_recomendaciones` = `cct × id_ciclo`.
- **Decisión de diseño DEC-010 para C2:** los tres datasets leen **solo el grano `escuela`**
  `(p.grano IS NULL OR p.grano = 'escuela')` + JOIN por `cct`. La proyección `municipio × nivel`
  jamás se reparte entre escuelas; donde no hay fila de escuela, `cobertura_prediccion = 'SIN_DATO'`.
- Reglas heredadas reiteradas: R1 (ML por LEFT JOIN), R2 (`SIN_DATO` nunca 0; COALESCE solo para
  etiquetar categoría), R3 (umbral 0.6), R7 (filtros AC-002.2).
- §8 contrato de dependencias: petición formal de cambio a C1/C3 con comportamiento de bloqueo
  (banderas de cobertura, no ceros).

### Capa semántica (`superset/semantic/`)
- **`db06_cubo_predicciones.sql`** — componentes aditivos DEC-008/DEC-009:
  `escuelas`, `matricula_total`, `variacion_x_matricula`, `suma_completitud`,
  `suma_variacion_proyectada`, `escuelas_con_prediccion`, `suma_indice_riesgo`,
  `escuelas_en_riesgo` (FILTER `>= 0.6`), `cobertura_prediccion`. Sin promedios precalculados.
- **`db06_predicciones_escuela.sql`** — grano del hecho: cada escuela con `indice_riesgo`,
  `variacion_proyectada`, `probabilidad`, `en_riesgo` (NULL sin predicción, jamás FALSE) y
  `rango_riesgo` (cubetas 0.00-0.19 … 0.80-1.00 para el pie de distribución).
- **`db09_cubo_recomendaciones.sql`** — espejo del cubo físico US-113 + `nombre_driver` vía
  `dim_driver`; `recomendacion_emitida` (único 0 permitido), `cobertura_recomendacion` y el
  riesgo de contexto por LEFT JOIN a predicciones (KPI-04, AC-002.5).
- **`metrics_db06_db09.yaml`** — 3 datasets, 3 filtros globales (ciclo/entidad/nivel, entidad por
  `nombre_entidad`, `cve_ent` expuesta como llave), razones SUM/SUM con NULLIF, cobertura
  declarada en toda métrica de ML, KPIs trazados: **KPI-01/02/05/12 en DB-06, KPI-11/07/04/03/01
  en DB-09**. `variacion_proyectada_promedio` y `indice_riesgo_promedio` dividen entre
  `escuelas_con_prediccion` (denominador visible), nunca entre el total.

### Tableros declarativos (`superset/dashboards/`)
- **`db06_predicciones.yaml`** (slug `db06-predicciones`, 7 charts): 4 tiles KPI (KPI-01/02/12 +
  % cobertura), observada vs proyectada por ciclo, pie de distribución de riesgo y ranking
  municipal por escuelas en riesgo.
- **`db09_recomendaciones.yaml`** (slug `db09-recomendaciones`, 7 charts): 4 tiles
  (KPI-11/prioridad ALTA/% recomendadas/KPI-04), pie por prioridad, bar por driver dominante
  (KPI-07 con categoría SIN_DATO agrupada) y la tabla "Escuelas a intervenir (mayor riesgo)".
- Sin cambios en `sync_semantic_layer.py`: descendió por glob y `ensure_chart()` ya compara
  `datasource_id` (fix BUG-011 del 25-ago evita repuntar charts homónimos).

### Mock local (`superset/mock/gold_ml_outputs_mock.sql`)
- Añadida **`grano TEXT DEFAULT 'escuela'`** en el CREATE TABLE **y** como ADD COLUMN IF NOT
  EXISTS (aditivo, legacy-safe, DEC-010): las filas ya existentes se tratan como grano escuela.

### Pruebas (`tests/test_semantic_db06_db09.py`, 50 casos)
- Espejo de las reglas de `test_semantic_db01_db02.py`/`db03_db04` sobre los 3 datasets:
  `SIN_DATO` nunca 0, ML por LEFT JOIN con llave completa (`cct`,`id_ciclo`)+`modelo='ML-01'`,
  **filtro de grano escuela (DEC-010) explícito**, umbral 0.6, `en_riesgo` nulo sin predicción,
  componentes aditivos sin promedios precalculados, razones con NULLIF en el YAML, KPIs trazados,
  charts→datasets/métricas declaradas, tiles KPI (ancho ≤ 3), filtros nativos sobre columnas
  reales, mock aditivo e idempotente, formatos d3 cubriendo el YAML.

## Verificación
- `pytest tests/test_semantic_db06_db09.py` → **50 passed**.
- Suite completa → **418 passed, 5 skipped, 4 failed** (los 4 fallos son `test_validacion_sesnsp.py`/
  `test_validacion_sinaica.py` por **incompatibilidad ambiental de great_expectations con el
  intérprete del venv**, preexistente y ajeno a esta historia).
- `ruff check tests/test_semantic_db06_db09.py` → limpio.
- `vault_lint.py` → el único bloqueante es `PLAN_US204_DB06_DB09_TMP.md` (archivo temporal de
  trabajo, se borra antes del PR).
- **Validación en vivo:** ✅ completada al levantar Docker (ver sección completa abajo).

### Validación en vivo (end-to-end, 27-ago)
Ambiente: `faro-postgres` (Postgres 16, puerto host **55432**; el 5432 lo ocupa `genbi-postgres-1`
de otro proyecto) + `faro-superset` healthy. Se cargó `superset/mock/gold_ml_outputs_mock.sql`
(idempotente, INSERT 0 0; ALTER aditivo `grano` → 22/22 filas `'escuela'`).

- **Sync:** `POSTGRES_HOST=localhost POSTGRES_PORT=55432 python superset/sync_semantic_layer.py`
  → datasets `db06_cubo_predicciones`, `db06_predicciones_escuela`, `db09_cubo_recomendaciones`
  + métricas + charts (ids 41–55) + tableros `db06-predicciones` (8 charts) y
  `db09-recomendaciones` (7 charts) sincronizados por importación v1.
- **Guardia BUG-011 verificada:** los charts homónimos **ajenos quedaron intactos** (KPI-01
  existente en db04 → se creó copia id=41; KPI-04 → copia id=52). No se tocó ningún chart de
  DB-01/02/03/04.
- **`--validar-datos`:** 15/15 charts `✓ datos OK`. Cifras contra la BD: 25 escuelas /
  25 filas hecho, 9 municipios, 22 predicciones, 22 recomendaciones (`recomendacion_emitida=1`
  22/22).
- **R2/cobertura real:** las 3 escuelas del municipio 09002 sin predicción → filas del cubo con
  `cobertura_prediccion = 'SIN_DATO'` (nunca 0). "Distribución del riesgo proyectado" 6 filas
  (5 cubetas 0.00–0.19…0.80–1.00 + SIN_DATO), "Recomendaciones por prioridad" 4 (ALTA 7 / MEDIA 7
  / BAJA 8 / SIN_DATO), "Drivers dominantes (KPI-07)" 7 (D1–D6 + SIN_DATO), "Escuelas a intervenir"
  top 10 por riesgo, "Ranking municipal" 9.
- **Filtros AC-002.2:** ambos tableros con 3 filtros nativos ligados
  (`Ciclo escolar`→`id_ciclo`, `Entidad`→`nombre_entidad`, `Nivel educativo`→`nivel`) sobre sus
  datasets (json_metadata del metadato SQLite de Superset).
- URLs: http://127.0.0.1:8088/superset/dashboard/db06-predicciones/ y
  http://127.0.0.1:8088/superset/dashboard/db09-recomendaciones/

#### Hallazgo preexistente (NO de esta historia) — bloquea el sync serial de DB-05/08
`superset/semantic/db05_cubo_driver.sql:105` y `db08_cubo_pivot.sql:86` referencian
`gold.dim_driver.fuente` (`nivel_geografico` en el spec §3.3/§8 de DB-05). El seed canónico
`dbt/seeds/dim_driver.csv` **sí** trae `fuente/cobertura/nivel_geografico`, pero el `gold.dim_driver`
materializado en el Postgres local quedó con el esquema viejo (`id_driver`,`nombre`) — además el
catálogo local fue sembrado por el MOCK con nombres largos ("Pobreza y rezago social"), divergente
del seed ("Pobreza"). Consecuencia: `POST /api/v1/dataset/` → HTTP 500 y el sync aborta antes de
db06/db09. **Mitigación temporal (sin tocar artefactos):** se movieron los 3 archivos de DB-05/08
fuera de `semantic/` durante el sync y se restauraron idénticos (git limpio). **Escalado:** C1 debe
re-materializar `gold.dim_driver` con `dbt seed` (conciliar nombres largos vs seed) para
desbloquear DB-05/08 **antes de US-213**.

## Decisiones de esta sesión
- Los SQL del dataset virtual quedan **acotados al grano escuela** de `gold.predicciones`
  (DEC-010) con el filtro legacy-safe `(grano IS NULL OR grano='escuela')`.
- Flujo futuro con cubos físicos: `db06_cubo_predicciones`→`gold.cubo_matricula` (DEC-009),
  `db09_cubo_recomendaciones`→`gold.cubo_recomendaciones` (US-113); `db06_predicciones_escuela`
  queda como capa de detalle sin agregar (igual que `db02_puntos_escuela`).
- **AVISO al PM (Edgar):** `Traceability_Matrix.md` (REQ-002) y `04_UX_Design/_index.md` son
  🟡 compartidos → la fila de `test_semantic_db06_db09` ✅ y el alta del Cube_Specs en el índice
  quedan pendientes de merge de esta rama (se hicieron en PR); confirmar para no pisar lo que
  consoliden otras células.

## Próximo paso recomendado
1. ✔ Validación en vivo completa (Docker + mock + sync + AC-002.2 end-to-end).
2. PR `feat/manuel-reinada-us204-db06-db09` → plantilla → revisión del PM.
3. Borrar `PLAN_US204_DB06_DB09_TMP.md` antes del merge (ya borrado en sesión).
4. Al consolidar el PM: fila REQ-002 con `test_semantic_db06_db09` ✅ (50 casos) y lienzo MOC-04.
5. **Acción transversal:** reportar a C1/PM el hallazgo preexistente de `dim_driver` (seed vs
   materializado) que bloquea el sync de DB-05/08 antes de US-213.