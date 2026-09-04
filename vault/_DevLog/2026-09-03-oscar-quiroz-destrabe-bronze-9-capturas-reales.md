---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión larga: restauración de Bronze real, CONEVAL real, 9 capturas del manual"
touches: ["US-222", "US-223", "US-224", "BLOCK-004", "REQ-002"]
tags: [devlog]
---

# DevLog — 2026-09-03 — Se destraba Bronze real: 9 de 10 dashboards con datos reales

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/10_Risk_Governance/Blocker_Register]]

## Qué pedí

Diana confirmó el flujo real de CONEVAL (extractor oficial de Deni Garrido) para reemplazar el
dump que traía CONEVAL como datos de prueba. Pedí ejecutarlo paso a paso, explicando cada paso
antes de correrlo, dado el antecedente de la sesión anterior (un `dbt run` sin cuidado rompió
`gold.cubo_completitud` como efecto colateral).

## Qué hizo la IA

- Restauró `bronze_real_2026-09-03.dump` de Diana (Camino B de BLOCK-004): `pg_restore` falló dos
  veces por versión de archivo (1.16, más nueva que el cliente del contenedor); funcionó con un
  cliente `postgres:latest` (18.6) montando `~/Downloads` directamente, con un único warning
  ignorable (`transaction_timeout`, parámetro que no existe en Postgres 15). Verificado:
  `bronze.cct_siged_202608` (385,175 filas) y `bronze.formato911_historico` (1,373,580 filas)
  reales.
- Corrió el extractor real de CONEVAL: `extractor_coneval.py` descargó los 2 productos oficiales
  de `coneval.org.mx` (URL validada en el propio script) y generó Parquet en `data/bronze/coneval/`
  (gitignored). `cargar_bronze_coneval_real.py --producto ambos` los cargó:
  `bronze.coneval_irs_2020` (2,472 filas) y `bronze.coneval_pobreza_2020` (2,483 filas), con las
  columnas hasheadas reales que `rezago_municipio.sql` necesita — confirmado antes de seguir.
- `dbt run --select rezago_municipio dim_municipio cubo_pipeline` (acotado, antes de arriesgar todo
  Gold): `rezago_municipio` y `dim_municipio` **materializaron**; `cubo_pipeline` falló por
  `bronze.conagua_presas` — un blocker nuevo y distinto (CONAGUA/DS-06, no CONEVAL).
- `dbt run` completo: **22 de 24 modelos en verde**. `gold.fact_escuela_ciclo` se reconstruyó desde
  datos reales (132,566 filas), resolviendo de paso el desajuste de CCTs que había roto
  `cubo_completitud` la sesión anterior. Materializaron `cubo_completitud`, `cubo_matricula`,
  `cubo_riesgo_territorial`, `cubo_driver`, `cubo_escuela_360`, `cubo_pivot`,
  `cubo_recomendaciones`, `cubo_comparador_municipio`. Solo `agua_region` (Silver) y
  `cubo_pipeline` (Gold) siguieron fallando, ambos por CONAGUA.
- `pytest tests/ -q`: 840 passed, 7 skipped. `git status`: limpio (todo el trabajo fue en Postgres
  local, nada toca el repo hasta este commit).
- `python superset/sync_semantic_layer.py`: **9 de 10 tableros registrados** (DB-01…DB-09). DB-10
  siguió fallando, aislado a `conagua_presas`. Un reinicio de Superset (`docker compose restart`,
  workaround ya documentado en `superset/README.md`) resolvió 3 tableros que quedaron en
  `ERR_EMPTY_RESPONSE` tras tanta actividad de sync seguida.
- Tomó las 8 capturas reales restantes con Playwright (login real, sin hardcodear credenciales) y
  las insertó en `Manual_Usuario_Dashboards.md`, junto con la de DB-07 ya existente.

## Qué revisé yo

- Revisé cada captura antes de darla por buena: encontré que `db05-analisis-driver.png` solo
  mostraba el spinner de carga (36 charts, el tablero más pesado) — la retomé con más tiempo de
  espera y confirmó datos reales.
- Verifiqué con SQL directo, no solo con la salida de `dbt run`, que `bronze.coneval_irs_2020` y
  `coneval_pobreza_2020` tienen las columnas hasheadas exactas (`c_b9548dbd414b`, etc.) antes de
  intentar el `dbt run` acotado.
- Detecté y documenté con honestidad, no oculté, que los KPIs de predicción/recomendación (ML-01/
  ML-02) siguen en SIN_DATO en las 9 capturas — el mock de ML no se refrescó contra el catálogo
  real de 77,712 escuelas. Lo dejé explícito en cada sección del manual en vez de presentarlo como
  "completo".
- Confirmé `git status` limpio antes y después de cada bloque de trabajo en Postgres/Docker.

## Qué falta / bloqueos

- **DB-10 (US-223):** único tablero sin registrar. Bloqueo aislado a `bronze.conagua_presas`
  (CONAGUA/DS-06) — dependencia de **Emilio Galnares**, no de Diana/Deni. Reportado en
  `Blocker_Register.md` (BLOCK-004, actualizado).
- **Números de predicción/recomendación** en las 9 capturas: SIN_DATO por el mock de ML
  desactualizado — refrescarlo (o esperar salidas reales de Célula 3) es lo único que falta para
  que el manual muestre el diferenciador prescriptivo del proyecto con datos completos.
- El mapa de DB-07 (KPI-06) sigue sin autozoom — detalle cosmético ya documentado, no bloqueante.

## IDs tocados

US-222, US-223, US-224, BLOCK-004, REQ-002
