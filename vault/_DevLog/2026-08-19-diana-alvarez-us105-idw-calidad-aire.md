---
project: "FARO"
date: "2026-08-19"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "~2h"
touches: ["US-105"]
tags: [devlog, gold, dbt, us105, idw, driver-d6]
---

# US-105 — Interpolación IDW de D6 (calidad del aire) hacia cada escuela

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

Implementé la interpolación IDW (Inverse Distance Weighting) que convierte D6 (calidad del
aire, SINAICA/DS-05) de `SIN_DATO` universal a un valor real por escuela, cerrando el diseño
documentado en [[vault/03_Architecture/ADRs/ADR-006-idw-calidad-aire-agua|ADR-006]]:

- Grano por `cct` (escuela), usando lat/lon real de `dim_escuela`/`silver.escuela` — no un
  centroide de municipio inventado (decisión tomada tras revisar que `dim_driver.csv` ya
  declaraba `nivel_geografico = municipio`, tarea previa a esta sesión; se corrigió a `escuela`).
- Radio válido 15 km, ponderación IDW clásica (potencia 2), distancia por Haversine.
- Solo lecturas de PM2.5 marcadas válidas por la propia API SINAICA (`dato_valido = 1`).
- Fuera de radio o sin lat/lon real → `SIN_DATO` explícito (nunca cero, nunca nulo silencioso).
- Aplicado en los dos modelos Gold que ya traían D1-D4 reales: `fact_escuela_ciclo.sql` y
  `features_escuela.sql` (mismo patrón de CTEs de normalización dentro de Gold, consistente
  con D1/D2).

## Evidencia

- Fixtures nuevos: `tests/fixtures/generate_bronze_sinaica_fixtures.py` (4 estaciones,
  10 lecturas horarias de prueba, incluyendo casos de 2 estaciones dentro de radio, 1 estación
  sola y 1 estación fuera de radio para ejercitar la rama `SIN_DATO`).
- `src/ingesta/cargar_bronze_fixture.py` extendido con los esquemas `sinaica_estaciones` /
  `sinaica_observaciones`. Se encontró y corrigió un bug real en el camino: las columnas
  camelCase de SINAICA (`redesId`, `municipioId`, `estadoId`, `fechaIniDatos`) se creaban
  citadas en el DDL pero se insertaban sin citar, y Postgres las plegaba a minúsculas —
  `UndefinedColumn` al cargar. Corregido citando también las columnas del INSERT.
- `dbt run --select silver.escuela silver.aire_estacion dim_escuela dim_municipio
  fact_escuela_ciclo features_escuela`: 6/6 modelos, sin errores.
- `dbt test` (mismo `--select`): **53/53 PASS, 0 ERROR**.
- Verificación manual: `gold.fact_escuela_ciclo` queda con `d6_cobertura = 'OK'` en 1 escuela
  (la única, en este fixture de prueba, con estaciones SINAICA dentro de los 15 km) y
  `SIN_DATO` en las 24 restantes — correcto, no es un hueco nuevo, es la regla del proyecto
  aplicada a un radio real.

## Pendiente / fuera de alcance de esta sesión

- **D5 (agua, CONAGUA/DS-06)** sigue en `SIN_DATO` explícito: DS-06 (dueño Emilio Galnares Ruiz)
  no ha completado su prueba de descarga real, no hay `bronze.conagua` con datos. El mismo
  patrón IDW queda listo para reutilizarse ahí en cuanto haya datos.
- El **índice de confianza** de la interpolación (`1 - distancia/radio`) se calcula pero no se
  expone como columna nueva en `features_escuela`/`fact_escuela_ciclo` — es un contrato
  compartido con Andrés González Habib (C3); queda documentado como pendiente explícito en
  ADR-006, a decidir con él antes de tocar el esquema.

## Trazabilidad

- Historia: US-105 · Requisito: REQ-001 (AC-001.6)
- Decisión: [[vault/03_Architecture/ADRs/ADR-006-idw-calidad-aire-agua|ADR-006]]
- Archivos: `dbt/models/gold/fact_escuela_ciclo.sql` · `dbt/models/gold/features_escuela.sql` ·
  `dbt/models/gold/_gold__sources.yml` · `dbt/seeds/dim_driver.csv` ·
  `src/ingesta/cargar_bronze_fixture.py` · `tests/fixtures/generate_bronze_sinaica_fixtures.py`

→ [[vault/_DevLog/_index|Volver al índice]]