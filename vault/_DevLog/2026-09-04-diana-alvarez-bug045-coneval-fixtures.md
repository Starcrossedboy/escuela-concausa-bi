---
project: "FARO"
date: "2026-09-04"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "claude-sonnet-5"
session_duration: "fix de BUG-045 (fixtures CONEVAL)"
touches: ["BUG-045", "US-112", "US-113", "REQ-001", "REQ-002", "DS-07"]
tags: [devlog, bug045, coneval, fixtures, bronze, silver]
---

# BUG-045 — fixtures de CONEVAL alineados al esquema real

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/06_Quality_Testing/Bug_Register]]

## Qué estaba roto

Marina García lo encontró el 3-sep reconstruyendo su ambiente desde cero, Luis Téllez lo validó
claim por claim el 4-sep y lo registró como **BUG-045** (`high`, owner Célula 1). El único
fixture de CONEVAL del repo (`tests/fixtures/bronze_coneval_sample.csv`) emitía el esquema
**viejo** (`cve_mun, entidad, municipio, indice_rezago_social, grado_rezago, pobreza_pct`),
anterior a la migración de Deni al extracto oficial. `dbt/models/silver/rezago_municipio.sql`
exige el esquema **real**, con columnas hasheadas (`c_b9548dbd414b`, `c_deef5d1bd71a`…). Sin un
fixture compatible, nadie puede construir `silver.rezago_municipio` desde el repo → sin él no hay
`gold.dim_municipio` → sin él no se materializa ningún cubo → sin cubos no funciona ningún
tablero. Reproducido corriéndolo, no deducido: `column "c_b9548dbd414b" does not exist`. CI no lo
atrapa porque `dbt-contract` solo corre `dbt parse`.

## Arreglo aplicado

Se tomó el camino de **extender el generador** (una de las dos rutas que propuso Luis en el
registro), consistente con el patrón que ya usan las demás fuentes:

- `src/ingesta/cargar_bronze_fixture.py`: se quitó la entrada `"coneval"` (esquema de una sola
  tabla, ya huérfano — ningún source de dbt apunta a `coneval_v2`) y se agregaron
  `"coneval_irs"` / `"coneval_pobreza"` a `ESQUEMAS`, con las columnas hasheadas reales y
  conflicto de unicidad por `(_source, _ingested_at, <claves>)`.
- `tests/fixtures/generate_bronze_drivers_fixtures.py::generar_coneval`: reescrito para emitir
  **dos** archivos (`bronze_coneval_irs_sample.csv`, `bronze_coneval_pobreza_sample.csv`) con el
  esquema real, reutilizando los mismos 12 municipios sintéticos de los generadores hermanos.
- Se corrió el generador y se borró el fixture huérfano `bronze_coneval_sample.csv`.

**El mapeo hash → columna no se adivinó.** Se tomó de los manifiestos reales que la propia carga
de DS-07 de ayer produjo en el ambiente de Diana
(`data/bronze/coneval/manifests/ds07_postgres_columns_{irs,pobreza}_2020.json`, artefactos
locales, no versionados) — cubre las 9 columnas completas, no solo las 4 que ya estaban
documentadas en el hallazgo original.

No se tocó `src/ingesta/cargar_bronze_coneval_real.py` (el loader de producción): ya emite este
esquema correctamente y nunca tuvo el bug — es una arquitectura intencionalmente distinta
(columnas dinámicas por Parquet, sin `UNIQUE`) de la del cargador genérico de fixtures.

## Verificación

`device_bash` no tiene Docker ni alcanza `127.0.0.1:5432`, así que esto se verificó a nivel de
esquema, no contra Postgres real: ambos CSV nuevos, leídos con
`pd.read_csv(dtype=str, keep_default_na=False)`, no tienen columnas faltantes contra lo que el
modelo exige — 12 filas cada uno, 1 fila `SIN_DATO` para ejercitar cobertura parcial.
`tests/test_cargar_bronze_fixture_conteo.py` (único test existente sobre el módulo) solo usa
`esquema="cct"`, sin riesgo de romperse. `vault_lint.py` en verde.

**Pendiente en máquina con Docker/Postgres** (la propia Diana, antes de dar el fix por cerrado
del todo): `cargar_bronze_fixture.py --esquema coneval_irs`/`coneval_pobreza`,
`dbt run --select rezago_municipio` + `dbt test`, y `pytest tests/ -q` completo.

## Registro y trazabilidad

`Bug_Register.md`: BUG-045 pasa de `open` a `fixed`, con el detalle del arreglo en
§Arreglo aplicado (fila resumen línea 60 y sección detallada actualizadas).
`Traceability_Matrix.md`: nueva entrada de evidencia incremental del 2026-09-04.

## Fuera de alcance de este fix

La **guarda de CI** propuesta en el propio registro (una prueba que compruebe, para cada
`source` de dbt, que existe un fixture con las columnas que el modelo Silver correspondiente
referencia) **no se implementó aquí** — cubriría la clase de error, no solo esta instancia, pero
es una decisión de alcance mayor de Célula 1 que se deja pendiente por tiempo (demo el 9-sep).
