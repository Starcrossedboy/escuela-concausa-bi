---
project: "FARO"
date: "2026-08-19"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "sesión de trabajo — US-104 features_escuela"
touches: ["US-104", "US-103"]
tags: [devlog, gold, dbt, us104]
---

# DevLog — US-104: gold.features_escuela

**Fecha:** 2026-08-19
**Autora:** Diana Aracely Alvarez Varela (Célula 1, Tech Lead)
**Asistencia de IA:** Sí — Claude (Cowork), para diseño del modelo, fixtures de prueba y depuración.
**Historia:** US-104 (tabla de features para ML), S3, vence 2026-08-23. Registrada como RISK-004 en el Risk Register (bloqueaba ML-01/ML-02 de Héctor).

## Qué se construyó
`dbt/models/gold/features_escuela.sql` — grano `cct x id_ciclo`, contrato Data_Model.md §5.3.

Estado real de los 6 drivers en esta primera versión:
- **D1 pobreza** — real, `silver.rezago_municipio` (DS-07) por `cve_mun`
- **D2 inseguridad** — real, `silver.delitos_municipio` (DS-04) por `cve_mun`, agregado sin alinear meses al ciclo escolar todavía (simplificación documentada en el modelo)
- **D3 infraestructura / D4 conectividad** — real, `silver.cemabe` (DS-03) por `cct`, según ADR-004
- **D5 agua / D6 aire** — `SIN_DATO` explícito: CONAGUA/SINAICA no traen `cve_mun` todavía; el join espacial/IDW es alcance de US-105

Se agregaron también: 3 fuentes nuevas en `_gold__sources.yml` (cemabe, rezago_municipio, delitos_municipio), tests en `_gold__models.yml` (not_null en llaves, accepted_values OK/SIN_DATO en las 6 coberturas) y un test singular de unicidad de grano (`unique_features_escuela_cct_ciclo.sql`).

## Bugs encontrados y corregidos validando
1. Igual que en `dim_tiempo.sql` (US-103): `Data_Model.md` documenta `matricula_total`, pero `silver.matricula` (US-111, Deni) la entrega como `alumnos_total`. Aliaseado con nota; pendiente reconciliar el nombre canónico con Deni/Edgar.
2. En `src/ingesta/cargar_bronze_fixture.py`: `pandas.read_csv(..., dtype=str)` convertía celdas vacías del CSV en `NaN`, y ese `NaN` se insertaba en Postgres como texto `'NaN'` — que sí castea a número, disfrazando un SIN_DATO como dato real con cobertura `OK`. Corregido con `keep_default_na=False`. Afectaba a cualquier fixture futuro del equipo con celdas vacías, no solo a este.

## Validación
Fixtures nuevos y anonimizados (≤500 filas): `bronze_cemabe_sample.csv` (72), `bronze_coneval_sample.csv` (12), `bronze_sesnsp_sample.csv` (72), y `bronze_formato911_ciclo_anterior_sample.csv` (25, necesario para que el cálculo de `target_variacion_matricula` con `LAG()` tuviera ciclo anterior real que comparar).

Resultado: `dbt run` → `gold.features_escuela` con 25 filas reales (no solo `dbt compile`). `dbt test` → 11 de 11 en verde.

## Pendientes / coordinación
- 🟡 `gold.features_escuela` es tabla compartida con Andrés González Habib (C3) por Agent Context — avisarle antes de que Héctor empiece a consumirla en serio para ML-01/ML-02.
- Reconciliar con Deni/Edgar el nombre canónico `matricula_total` vs `alumnos_total` (mismo pendiente que dejó US-103).
- D5/D6 quedan en SIN_DATO hasta que US-105 entregue el join espacial de CONAGUA/SINAICA.
- Actualizar mi propio sprint board / Execution_Status con el avance de hoy.