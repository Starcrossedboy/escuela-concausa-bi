---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude (chat)"
session_duration: "sesión única: US-223 DB-10 monitor del pipeline"
touches: ["US-223", "US-201", "REQ-002", "DOC-CUBESPEC-DB10", "DOC-SCREENSPECS"]
---

# DevLog — 2026-08-30 — US-223: DB-10 Monitor del pipeline

## Qué pedí

Construir el entregable de US-223 (estado de la ingesta por fuente, KPI-13),
aplicando la misma disciplina de US-222: verificar el contrato real de
`gold.cubo_pipeline` antes de escribir SQL, sin invertir tiempo en construir
sobre algo que pudiera estar bloqueado o a punto de cambiar (dado que el
mismo día se mergeó PR #134/US-205, que reescribió 13 datasets virtuales).

## Qué generó la IA

- `superset/semantic/db10_cubo_pipeline.sql`: dataset a grano detallado
  (`id_fuente × fecha_ingesta`), casi un `SELECT *` sobre `gold.cubo_pipeline`
  (ya materializado por C1, US-113), con 2 columnas calculadas (`es_ok`,
  `es_sin_dato`) para cumplir el guardián de columnas ausentes de
  `test_semantic_repunteo_cubos` (US-205), que no reconoce literales de
  texto en mayúsculas dentro de expresiones `COUNT(*) FILTER (...)`.
- `superset/semantic/metrics_db10.yaml`: capa semántica con la única
  métrica del catálogo (KPI-13) más 3 métricas de apoyo (`fuentes_ok`,
  `fuentes_sin_dato`, `ultima_ingesta`).
- `tests/fixtures/generate_fixtures_db10.py` y
  `tests/test_db10_monitor_pipeline.py`: fixtures sintéticas replicando el
  esquema real confirmado en `dbt/models/gold/cubo_pipeline.sql`, y 5
  pruebas que leen el SQL de producción directamente.
- `vault/04_UX_Design/Cube_Specs_DB10.md`: documentación del contrato semántico.

## Qué revisé yo

- Confirmé el contrato real de `gold.cubo_pipeline` leyendo el modelo dbt
  antes de escribir cualquier SQL de Superset (mismo patrón que US-222).
- Intenté materializar el modelo con `dbt run --select cubo_pipeline`: falló
  por `relation "silver.matricula" does not exist` — a diferencia de
  `cubo_completitud` (US-222), este modelo depende de 8 tablas Silver
  distintas, todas bloqueadas por la falta de Bronze en este ambiente. No
  hay ninguna dependencia "con suerte" ya resuelta como en US-222.
- Corrí la suite completa tras el `git pull` de 14 commits (incluyendo el
  merge de PR #134/US-205) y encontré un fallo real: el test guardián de
  Manuel (`test_semantic_repunteo_cubos`) rechazó mi YAML porque su
  detector de columnas confundía el literal `'SIN_DATO'` con un
  identificador. Corregí exponiendo columnas booleanas calculadas en el SQL
  (`es_ok`, `es_sin_dato`) en vez de usar `COUNT(*) FILTER (WHERE
  columna = 'literal')` directo en la métrica — mismo resultado, compatible
  con el guardián.
- Actualicé el test propio para desempaquetar las 2 columnas nuevas tras el
  ajuste del SQL.
- Corrí la suite completa (648 passed) y `vault_lint.py` (limpio) antes de
  documentar el bloqueo como definitivo.

## Qué falta / bloqueos

- **Bloqueo real, documentado, no resuelto aquí:** validación contra
  Postgres real pendiente de que se cargue Bronze completo en el ambiente
  — mismo bloqueo estructural que US-222, sin solución disponible desde
  esta historia.
- Pendiente construir los charts/dashboard de DB-10 una vez que el bloqueo
  de Bronze se resuelva.
- Con el mock que Manuel autorizó para US-222
  (`superset/mock/gold_ml_outputs_mock.sql`) pendiente de aplicar, y con
  el patch de consolidación de KPIs de US-221 pendiente de aplicar ahora
  que PR #134 ya se mergeó — ambos quedan como trabajo de seguimiento para
  la próxima sesión.

## IDs tocados

US-223, US-201, REQ-002, DOC-CUBESPEC-DB10, DOC-SCREENSPECS