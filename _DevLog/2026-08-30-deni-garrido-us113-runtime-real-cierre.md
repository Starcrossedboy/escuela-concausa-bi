---
project: "FARO"
date: "2026-08-30"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
session_duration: "cierre runtime real US-113"
touches: ["US-113", "DS-06", "DS-07", "ADR-007", "DB-10"]
tags: [devlog, us113, runtime, gold, cubos, datos-reales]
---

# US-113 — cierre runtime real de los 9 cubos Gold

→ [[_DevLog/_index|Volver al índice]] · [[12_Roadmap_Sprints/Sprints/1-deni-garrido-fragoso]]

## Objetivo

Cerrar la evidencia runtime pendiente de US-113 sin ocultar dependencias ni reemplazar
fuentes reales por datos sintéticos.

## Dependencias resueltas antes del cierre

- **DS-07 CONEVAL:** descarga oficial real, Bronze/Postgres y
  `silver.rezago_municipio` nacional con 2,469 municipios.
- **ADR-007:** `target_variacion_matricula` normalizado a fracción antes de publicar ML.
- **DS-06 CONAGUA/IMTA:** snapshot real de 180 presas en `bronze.conagua_presas`;
  DB-10 registra la ingesta real y D5 permanece `SIN_DATO` explícito mientras no exista
  una conformación geográfica/temporal válida.
- **`gold.dim_driver`:** seed canónico de 6 drivers materializado.
- **ML Gold:** `publicar_gold --desde-gold` ejecutado sobre `gold.features_escuela`
  real mediante UPSERT canónico, sin `DELETE`/`TRUNCATE`.

## Evidencia runtime final

- `dbt run` de ancestros + 9 cubos: **PASS**
- tests dbt de cubos: **134/134 PASS**
- cubos faltantes: **0**
- cubos vacíos: **0**

| Cubo | Filas | Estado |
|---|---:|---|
| `cubo_matricula` | 90 | OK |
| `cubo_riesgo_territorial` | 90 | OK |
| `cubo_escuela_360` | 145 | OK |
| `cubo_comparador_municipio` | 90 | OK |
| `cubo_driver` | 540 | OK |
| `cubo_completitud` | 540 | OK |
| `cubo_pivot` | 870 | OK |
| `cubo_recomendaciones` | 145 | OK |
| `cubo_pipeline` | 9 | OK |

Cierre emitido por la automatización:

`OK_US113_RUNTIME_REAL`

## Alcance y transparencia

- La validación se ejecutó contra PostgreSQL local reproducible.
- No se modificaron cubos para esconder dependencias.
- No se usaron fixtures nuevos para forzar el runtime.
- DS-06 queda real para trazabilidad de ingesta/DB-10; **D5 no se declara resuelto** y
  conserva cobertura `SIN_DATO` hasta disponer de una fuente/regla oficial compatible.
- Los reportes runtime `.txt/.json` permanecen locales y **no se versionan**.

## Cierre

US-113 cuenta con evidencia runtime materializada para los 9 cubos y sus tests dbt.
La actualización de `02_Requirements/Traceability_Matrix.md` queda para Edgar/PM,
dueño del artefacto y responsable de su mantenimiento.
