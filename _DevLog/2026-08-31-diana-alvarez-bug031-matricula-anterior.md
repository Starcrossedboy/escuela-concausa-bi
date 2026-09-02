---
project: "FARO"
date: "2026-08-31"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "~2h"
touches: ["BUG-031"]
tags: [devlog, gold, matricula, bug031, kpi02]
---

# BUG-031 (C1) — Exponer `matricula_ciclo_anterior` para la razón de sumas de KPI-02

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

**Contexto.** Marina García del Buey (C2) reportó BUG-031: KPI-02 «Variación de matrícula» pinta
−54.5 % donde el valor real es −0.19 % (factor de error 287), en seis tableros (DB-01, DB-02, DB-03,
DB-04, DB-06, DB-09). Causa raíz: `variacion_x_matricula = SUM(variacion_matricula * matricula_total)`
es un promedio ponderado de `variacion_matricula`, que no es una razón sino alumnos absolutos
(`matricula_total - matricula_ciclo_anterior`). El fix correcto no depende de ADR-007 y se expresa
solo en alumnos: `SUM(matricula_total) / NULLIF(SUM(matricula_ciclo_anterior), 0) - 1` — una razón de
sumas, no un promedio de razones. Requiere `matricula_ciclo_anterior`, que `fact_escuela_ciclo.sql` ya
calculaba en el CTE `con_anterior` (vía `lag()`) pero descartaba antes de llegar a `base`.

**Alcance de C1 según el registro (3 archivos):** exponer la columna en `fact_escuela_ciclo.sql` y
propagarla a `cubo_escuela_360.sql` y `cubo_comparador_municipio.sql` (DB-04).

**Alcance ampliado, encontrado antes de dar por cerrada la parte de C1.** Antes de tocar código,
grep exhaustivo (`grep -rln "variacion_x_matricula"` sobre `dbt/tests/` y `dbt/models/`) del mismo
patrón defectuoso encontró el **mismo defecto exacto**, sin documentar en el registro, en dos cubos
más:

- `cubo_matricula.sql` — alimenta DB-01 y DB-06, ambos ya listados como afectados por BUG-031.
- `cubo_riesgo_territorial.sql` — alimenta DB-02, también listado.

Un segundo grep, más amplio (todo el repo, excluyendo `/target/`), confirmó que no hay una cuarta
instancia — los únicos matches restantes son los archivos de capa semántica de Superset y las
pruebas Python, ambos ya escalados a C2/Manuel en el registro. Cada expansión de alcance se confirmó
con Diana antes de implementar.

**Fix aplicado (6 archivos):**

- `dbt/models/gold/fact_escuela_ciclo.sql` — `matricula_ciclo_anterior` expuesta en `base`,
  `con_municipio`, `ensamblado` y el `select` final.
- `dbt/models/gold/cubo_escuela_360.sql` — propagada.
- `dbt/models/gold/cubo_comparador_municipio.sql` — `variacion_x_matricula` reemplazada por
  `sum(f.matricula_ciclo_anterior) as suma_matricula_anterior`.
- `dbt/models/gold/cubo_matricula.sql` — mismo reemplazo (alcance ampliado, DB-01/DB-06).
- `dbt/models/gold/cubo_riesgo_territorial.sql` — mismo reemplazo (alcance ampliado, DB-02).
- `dbt/tests/cubo_matricula_fact_parity.sql` — `variacion_x_matricula` → `suma_matricula_anterior`
  en la CTE `esperado` y en la comparación del `where`.
- `dbt/models/gold/_gold__models.yml` — documentada `matricula_ciclo_anterior` con `not_null`.

Fuera de alcance de C1, escalado a C2 (Manuel Serranía): `metrics_db01_db02.yaml`,
`metrics_db03_db04.yaml`, `metrics_db06_db09.yaml` (migrar a razón de sumas) y retirar las dos
aserciones que hoy exigen `variacion_x_matricula` como si fuera requisito
(`test_semantic_db01_db02.py`, `test_semantic_db06_db09.py`).

## Cómo se probó

Sobre Postgres real (`escuela_concausa_db`, `docker compose up -d db`):
cd dbt && dbt run --full-refresh


`gold.fact_escuela_ciclo` y los 5 cubos tocados reconstruyen limpio: 148 (`fact_escuela_ciclo`,
`cubo_escuela_360`), 90 (`cubo_comparador_municipio`, `cubo_matricula`, `cubo_riesgo_territorial`)
filas. El único modelo que sigue en `SKIP` es `silver.agua_region` → `gold.cubo_pipeline`, gap
preexistente y ya documentado de DS-06/CONAGUA (`bronze.conagua_no_ingerido` no existe).

dbt test


`cubo_matricula_fact_parity` y `not_null_fact_escuela_ciclo_matricula_ciclo_anterior` en verde —
validan directamente el fix. De los 13 errores restantes del run completo:

- 7 son la cascada preexistente de DS-06/CONAGUA (`silver.agua_region` sin `bronze.conagua_no_ingerido`).
- 1 es el gap preexistente de DS-07/CONEVAL (`relationships` de `features_escuela.cve_mun` →
  `dim_municipio`, 112,747 filas — `dim_municipio` solo tiene 10 municipios reales de 317
  alcanzables).
- 2 se diagnosticaron en esta verificación: `cubo_recomendaciones_kpi11_parity` y
  `gold_ml_runtime_recomendaciones_fact_relationship`. Ninguno de los dos referencia
  `matricula_total`, `matricula_ciclo_anterior`, `variacion_matricula` ni `suma_matricula_anterior`
  (leídos ambos archivos completos). Ambos comparan `gold_ml_runtime.recomendaciones` (ML-02) contra
  el grano `(cct, id_ciclo)` de `fact_escuela_ciclo`, que excluye por diseño el primer ciclo
  observado de cada cct (filtro preexistente `where matricula_ciclo_anterior is not null` en el CTE
  `base` — no hay ciclo anterior contra el cual calcular la variación). Si ML-02 emitió
  recomendaciones para ese primer ciclo en algunas escuelas, esas filas quedan fuera de
  `fact_escuela_ciclo` y rompen la paridad/relación con `recomendaciones`. Confirmado con
  `git diff main -- dbt/models/gold/fact_escuela_ciclo.sql` que el fix de BUG-031 es puramente
  aditivo (solo agrega columnas a los `select`) y no toca esa cláusula `where` ni ningún `join`: el
  conjunto de `(cct, id_ciclo)` en `fact_escuela_ciclo` es idéntico antes y después del fix, así que
  estos 2 errores no pueden ser una regresión de este cambio.

Nota de proceso: un primer intento de `dbt run --select fact_escuela_ciclo+` falló por un error de
edición manual (VS Code duplicó la palabra `select` al pegar el cambio del `select` final), lo que
dejó los 5 cubos en `SKIP` y produjo conteos de `FAIL` enormes y sin sentido (2763, 926, 110342 filas)
en la corrida de `dbt test` subsecuente — artefactos de probar cubos no reconstruidos, no defectos
reales. Se corrigió el duplicado y se volvió a correr `dbt run --full-refresh` + `dbt test` **sin**
`--select`, sobre el DAG completo, para obtener una señal limpia; esos conteos desaparecieron por
completo en la corrida limpia.

`pytest`: 643 passed, 5 skipped — sin regresiones nuevas.

## Archivos tocados

- `dbt/models/gold/fact_escuela_ciclo.sql`
- `dbt/models/gold/cubo_escuela_360.sql`
- `dbt/models/gold/cubo_comparador_municipio.sql`
- `dbt/models/gold/cubo_matricula.sql`
- `dbt/models/gold/cubo_riesgo_territorial.sql`
- `dbt/tests/cubo_matricula_fact_parity.sql`
- `dbt/models/gold/_gold__models.yml`