---
project: "FARO"
date: "2026-08-16"
title: "US-111 · Cierre técnico Bronze a Silver"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
session_duration: "cierre US-111"
touches: ["US-111", "REQ-001", "DS-01", "DS-02", "DS-03", "DS-04", "DS-05", "DS-06", "DS-07", "DS-08"]
tags: [devlog, ai-assisted, sprint-2, celula-1, dbt, silver]
---

# DevLog — 2026-08-16 — Cierre técnico US-111 Bronze → Silver

> [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

Se completó la implementación dbt de `US-111` para las fuentes DS-01 a DS-08, respetando la arquitectura medallón y el alcance nacional de Bronze/Silver.

Modelos Silver implementados:

- `silver.matricula` — DS-01 Formato 911.
- `silver.escuela` — DS-02 Catálogo CCT.
- `silver.cemabe` — DS-03 CEMABE.
- `silver.delitos_municipio` — DS-04 SESNSP.
- `silver.aire_estacion` — DS-05 SINAICA.
- `silver.agua_region` — DS-06 CONAGUA.
- `silver.rezago_municipio` — DS-07 CONEVAL.
- `silver.poblacion_municipio` — DS-08 CONAPO.

También se implementaron macros reutilizables para homologación de:

- CCT a 10 caracteres.
- clave INEGI de entidad a 2 dígitos.
- clave INEGI municipal a 5 dígitos.
- clave municipal standalone para fuentes sin entidad separada.
- drivers binarios y política explícita `SIN_DATO`.

## Decisiones de ingeniería

- Bronze y Silver permanecen nacionales; `SCOPE_ENTIDADES` no se aplica en estas capas.
- Las llaves inválidas no se corrigen silenciosamente.
- La deduplicación conserva la ingesta más reciente mediante `_ingested_at`.
- Se conservan `_source` y `_source_url` para linaje.
- `SIN_DATO` no se sustituye por cero.
- DS-05 separa observaciones y catálogo de estaciones como contratos Bronze lógicos y hace join por `id_estacion`.
- DS-06 conserva región y coordenadas para una asignación espacial/IDW posterior.
- DS-07 preserva historia mediante `periodo_medicion` parametrizado; no utiliza `_ingested_at` como periodo del indicador.
- DS-08 parametriza la columna etaria de origen (`edad` / `grupo_edad`).

## Calidad y validación

- 8 modelos dbt registrados.
- 51 data tests registrados.
- 9 sources registrados.
- 482 macros disponibles al cierre.
- Compilación global `dbt compile` ejecutada sin errores.
- Tests declarativos para `not_null`, `unique` y `accepted_values` donde corresponde.
- Tests singulares para:
  - unicidad de granos compuestos;
  - formato de claves INEGI;
  - rangos horarios y geográficos;
  - conteos no negativos;
  - coherencia de cobertura `OK` / `SIN_DATO`.

## Dependencias / límites de validación

- La compilación utilizó variables temporales para fuentes Bronze cuyo identificador físico todavía no está confirmado.
- DS-04, DS-06, DS-07 y DS-08 mantienen dependencias upstream de ingesta/prueba real documentadas en sus contratos.
- DS-05 tiene prueba real de fuente, pero el contrato físico final de Bronze debe ser materializado por la historia responsable de ingesta.
- No se reporta `dbt build` end-to-end como aprobado mientras no existan todas las tablas Bronze físicas requeridas.
- Estos puntos no impiden la validación estática y compilación de la implementación dbt de US-111.

## Estado de US-111

- Implementación Bronze → Silver: completada.
- Compilación global: completada.
- Seguimiento de sprint actualizado a `95% · En curso`.
- Pendiente para cierre formal:
  - actualizar matriz de trazabilidad;
  - ejecutar `vault_lint.py`;
  - revisión Git;
  - commit/push;
  - abrir PR para revisión del Tech Lead.

## Evidencia

- Commit previo de avance: `257b58` — `feat(dbt): avance US-111 Bronze a Silver`.
- Rama: `feat/deni-fragoso-us-111`.
