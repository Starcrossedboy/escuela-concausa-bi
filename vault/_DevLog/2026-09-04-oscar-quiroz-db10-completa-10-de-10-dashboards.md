---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión: CONAGUA real, fix de FORMATO_D3, 10/10 dashboards"
touches: ["US-223", "US-224", "BLOCK-004", "REQ-002"]
tags: [devlog]
---

# DevLog — 2026-09-04 — DB-10 completa: los 10 dashboards con captura real

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/10_Risk_Governance/Blocker_Register]]

## Qué pedí

Antes de escribirle a Emilio Galnares por CONAGUA/DS-06, pedí verificar si sus historias
(US-121a…124a) ya estaban completas — lo estaban, `done` desde el 28-ago, con extractor y loader
reales ya construidos (`extractor_conagua.py`, `cargar_bronze_conagua_real.py`). Pedí revisar esos
scripts antes de correrlos, y luego ejecutar el plan completo de 5 pasos.

## Qué hizo la IA

- Revisó `extractor_conagua.py` (POST real a `sisuar.imta.mx/aplicacion/controlador/mapa.php`,
  dato público de IMTA, sin auth) y `cargar_bronze_conagua_real.py` (idempotente, sin
  `DROP`/`DELETE`, valida columnas requeridas) antes de correr nada.
- Confirmó con `dbt run --select cubo_pipeline` (acotado, antes de arriesgar todo Gold) exactamente
  qué necesitaba: solo `_source`/`_ingested_at`/`_source_url` de `bronze.conagua_presas` — la
  misma tabla que alimenta `silver.agua_region`/D5 es una fuente *distinta*
  (`bronze.conagua`/`conagua_no_ingerido`, placeholder falso a propósito por BUG-030) y no se toca.
- Ejecutó los 5 pasos: extraer (180 presas reales) → cargar → verificar en SQL directo → `dbt run`
  acotado (`gold.cubo_pipeline` → 10 filas) → `sync_semantic_layer.py` → captura.
- **Encontró un bug real durante el sync**, no en los datos: los 5 charts de DB-10 se crearon pero
  con "Metric 'filas' does not exist" — `FORMATO_D3` en `sync_semantic_layer.py` no tenía entrada
  para `formato: fecha` (única métrica de fecha del proyecto, `metrics_db10.yaml → ultima_ingesta`),
  así que `d3format` caía a cadena vacía y Superset rechazaba el PUT **completo** del dataset con
  HTTP 422 — ninguna de las 4 métricas se aplicaba, no solo la de fecha.
- Corrigió `FORMATO_D3` con `"fecha": "smart_date"`; probó, vio que un `big_number_total` interpreta
  el timestamp crudo como número ("​.527ms"); ajustó a `"%Y-%m-%d"`; mismo resultado. Tras 3
  intentos, con confirmación del usuario, aceptó el límite: `big_number_total` de Superset formatea
  con d3-format (numérico), no d3-time-format — no hay valor de `d3format` que arregle un
  `MAX(timestamp)` crudo en ese tipo de chart. Documentado con honestidad en el manual en vez de
  seguir iterando sin garantía.
- Escribió `tests/test_sync_formato_d3_cobertura.py` (3 casos): confirma que `fecha` está mapeado,
  que ningún valor de `FORMATO_D3` es cadena vacía, y que todo `formato:` usado en cualquier
  `metrics_*.yaml` del repo tiene entrada — guarda de no-regresión genérica, no solo para este caso.
- Insertó la captura real de DB-10 en `Manual_Usuario_Dashboards.md`, que llega a **10/10**.

## Qué revisé yo

- No asumí que "smart_date" funcionaría — lo probé, vi el resultado incorrecto, y lo corregí en vez
  de dejarlo así.
- Confirmé con SQL directo (no solo con la salida del script) que `bronze.conagua_presas` tiene
  180 filas con `_source = 'DS-06_CONAGUA_SINA'` antes de correr `dbt`.
- Verifiqué que `agua_region.sql`/D5 no se ve afectado por este cambio — sigue usando su propia
  fuente placeholder, sin tocar.
- Corrí la suite completa (855 passed) y `vault_lint` (limpio) antes de dar el trabajo por
  terminado.

## Qué falta / bloqueos

- **Ninguno de mi lado.** Los 10 dashboards están registrados y con captura real.
- **Límite cosmético conocido, no bloqueante:** el tile "Última ingesta" de DB-10 muestra
  ".527ms" en vez de una fecha legible — límite de `big_number_total` en Superset, documentado en
  el manual, no un dato faltante.
- Los KPIs de predicción/recomendación siguen SIN_DATO en las 10 capturas por el mock de ML
  desactualizado — fuera de mi alcance (Célula 3), ya documentado desde antes.

## IDs tocados

US-223, US-224, BLOCK-004, REQ-002
