---
id: DOC-CUBESPEC-DB10
title: "Cube Specs — DB-10 Monitor del pipeline"
owner: "Oscar Antonio Quiroz Lázaro"
status: approved
version: "1.0"
traces_up: ["vault/04_UX_Design/Screen_Specs", "US-223"]
traces_down: []
last_reviewed: "2026-09-02"
tags: [ux, dashboards, kpis, celula-2, pipeline]
---

# Cube Specs — DB-10 Monitor del pipeline

> Contrato semántico de DB-10: estado de la ingesta por fuente de datos.
> Implementa **US-223** (REQ-002), consumiendo el catálogo canónico de
> KPI-13 ya fijado en [[vault/04_UX_Design/Screen_Specs]] §4 (US-201, Manuel
> Serranía).

## 1. Fuente de datos

`gold.cubo_pipeline` (US-113, Diana Álvarez / Célula 1), materializado como
`materialized_view` en dbt (`dbt/models/gold/cubo_pipeline.sql`). Grano:
`id_fuente × fecha_ingesta`.

El modelo conserva las 8 fuentes esperadas del catálogo (DS-01…DS-08) como
filas de catálogo, incluso cuando una fuente no ha ingerido nada todavía:
en ese caso `cobertura_pipeline = 'SIN_DATO'` y `filas` queda `NULL` — nunca
se representa como cero ni la fuente desaparece de la lista.

## 2. Dataset

### `db10_cubo_pipeline` — grano por fuente y fecha de ingesta

Casi un `SELECT *` sobre el cubo materializado, con 2 columnas calculadas
agregadas para exponer componentes aditivos sin usar literales de texto
dentro de las expresiones de métrica (`es_ok`, `es_sin_dato`) — necesario
para pasar el guardián de columnas ausentes de `tests/test_semantic_repunteo_cubos.py`
(US-205, Manuel Serranía), cuyo detector de identificadores no reconoce
literales en mayúsculas dentro de una expresión `COUNT(*) FILTER (WHERE ...)`.

```sql
CASE WHEN cobertura_pipeline = 'OK' THEN 1 ELSE 0 END AS es_ok,
CASE WHEN cobertura_pipeline = 'SIN_DATO' THEN 1 ELSE 0 END AS es_sin_dato
```

Las métricas correspondientes usan `SUM(es_ok)` y `SUM(es_sin_dato)` en vez
de `COUNT(*) FILTER (...)` directamente en el YAML — mismo resultado,
compatible con el guardián.

**Filtros globales:** DB-10 es de alcance nacional y no aplica los filtros
de ciclo/entidad/nivel de AC-002.2 — su unidad de análisis es la fuente de
ingesta, no la escuela ni el territorio.

## 3. Validación realizada

- El SQL **no se pudo validar contra Postgres real** — ver bloqueo abajo.
- 5 pruebas automatizadas (`tests/test_db10_monitor_pipeline.py`) validan
  contra fixtures sintéticas que replican el esquema real confirmado
  leyendo `dbt/models/gold/cubo_pipeline.sql`: presencia de las 8 fuentes,
  que `filas` nunca se rellena con 0 en fuentes SIN_DATO, que `SUM(filas)`
  excluye correctamente esas fuentes, y que el grano no tiene duplicados.

## 4. Bloqueo conocido — validación contra Postgres real

`gold.cubo_pipeline` depende de 8 tablas Silver distintas (una por fuente:
matrícula, escuela, cemabe, delitos, aire, agua, rezago, población), y
**todas** dependen de que el esquema `bronze` esté cargado. En este
ambiente local, `dbt run` completo falla con errores de tablas Bronze
inexistentes, así que `cubo_pipeline` nunca pudo materializarse
(a diferencia de `cubo_completitud` en US-222, que tuvo la única
dependencia ya resuelta).

Mismo bloqueo de infraestructura documentado en US-222 — no es error de
este SQL, y no se simuló con datos inventados por la misma razón: no es
contrato que le corresponda definir a esta historia.

**Actualización 2026-09-03 — bloqueo reducido a una sola fuente, aislada.** De las 8 tablas Silver,
7 ya materializan con Bronze real (incluida `rezago_municipio`/CONEVAL, vía el extractor oficial
de Deni Garrido). Confirmado con `dbt run`: `gold.cubo_pipeline` **solo** falla por
`bronze.conagua_presas` (CONAGUA/DS-06) — dependencia de Emilio Galnares, no de Diana/Deni. Es el
único de los 10 dashboards que sigue sin registrarse en Superset; ver
[[vault/10_Risk_Governance/Blocker_Register]] (BLOCK-004).

**Actualización 2026-09-04 — bloqueo resuelto por completo.** Emilio Galnares ya tenía el extractor
real de CONAGUA listo desde el 28-ago (US-121a…124a, `done`) — solo faltaba correrlo en este
ambiente. `bronze.conagua_presas` cargado (180 presas reales), `dbt run --select cubo_pipeline`
materializa con **10 filas**. DB-10 registrado y vivo en Superset con captura real en
[[vault/04_UX_Design/Manual_Usuario_Dashboards]]. De paso se corrigió un bug real en
`sync_semantic_layer.py` (`FORMATO_D3` sin entrada para `formato: fecha`, hacía que ninguna
métrica del dataset se aplicara) — ver `tests/test_sync_formato_d3_cobertura.py`.

## 5. Trazabilidad

- **Implementa:** US-223 (REQ-002)
- **Consume:** [[vault/04_UX_Design/Screen_Specs]] (catálogo canónico KPI-13,
  US-201) · `gold.cubo_pipeline` (US-113, Diana Álvarez)
- **Bloqueo documentado:** validación contra Postgres real pendiente de que
  se resuelva la carga de Bronze en el ambiente (mismo bloqueo que US-222)