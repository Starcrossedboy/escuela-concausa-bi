---
project: "FARO"
date: "2026-08-19"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "sesión de trabajo — cierre de US-103"
touches: ["US-103", "US-104"]
tags: [devlog, gold, dbt, us103]
---

# DevLog — US-103: Estrella Gold completa (dim_escuela, dim_municipio, fact_escuela_ciclo)

→ [[_DevLog/_index|Volver al índice]]

**Fecha:** 2026-08-19
**Autora:** Diana Álvarez — Tech Lead, Célula 1 (Data Engineering & Quality)
**Historia:** US-103 — Modelo estrella Gold (Data_Model.md §4)
**Rama:** feat/diana-varela-us103-gold-estrella

## Resumen

Se completaron los últimos 3 de los 5 modelos del esquema estrella de Gold
(`dim_tiempo` y `dim_driver` ya estaban de sesiones anteriores):

- `gold.dim_municipio` — un registro por `cve_mun`, población (CONAPO) + nombres
  (CONEVAL), acotado a SCOPE_ENTIDADES.
- `gold.dim_escuela` — un registro por `cct`, identidad + infraestructura (CEMABE,
  con SIN_DATO explícito), acotado a SCOPE_ENTIDADES.
- `gold.fact_escuela_ciclo` — hecho central, un registro por `cct` x `id_ciclo`, con
  los 6 drivers (D1-D6) y `variacion_matricula`, acotado a SCOPE_ENTIDADES vía join a
  `dim_escuela`.

También se centralizó el filtro de alcance en un macro nuevo (`scope_entidades()`,
CDMX/Edomex/Nuevo León/Jalisco), y se corrigieron 2 bugs encontrados al validar con
datos reales:

1. `gold.features_escuela` (US-104) no traía el filtro SCOPE_ENTIDADES, aunque
   Data_Model.md §7 es explícito en que aplica a toda tabla Gold tipo "features".
2. `silver.escuela` (US-111) tronaba con `invalid input syntax for type double
   precision` cuando `latitud`/`longitud` venían vacíos — Data_Model.md §6 los
   documenta como nullable, así que era un caso real (escuela sin georreferenciar)
   sin manejar, no un dato corrupto.

## Validación

Corrido localmente con fixtures ampliados (`generate_bronze_cct_conapo_fixtures.py`,
nuevo; `generate_bronze_drivers_fixtures.py`, corregido para que `coneval` traiga
nombres reales de entidad/municipio en vez de códigos):

- Silver: `matricula` 97, `cemabe` 72, `rezago_municipio` 12, `delitos_municipio` 72,
  `escuela` 72, `poblacion_municipio` 36.
- Gold: `dim_tiempo` 2, `dim_municipio` 10, `dim_escuela` 60, `fact_escuela_ciclo` 25,
  `features_escuela` 25.
- `dbt test`: 88 PASS / 13 ERROR — los 13 son de `agua_region`/`aire_estacion`
  (DS-05/DS-06, fuera del alcance de esta historia, tablas que aún no existen en
  esta base local). Todo lo de esta historia (Silver tocado + los 5 modelos de la
  estrella Gold) pasó sin errores.

## Pendientes / a reconciliar

- Nombres de columna con Deni/Edgar: `matricula_total` (Data_Model.md) vs
  `alumnos_total` (silver.matricula real); `nombre_entidad`/`nombre_municipio`
  (Data_Model.md) vs `entidad`/`municipio` (silver.rezago_municipio real).
- D5 (agua) y D6 (aire) siguen en SIN_DATO explícito en `fact_escuela_ciclo`, mismo
  motivo que en `features_escuela`: falta el join espacial de CONAGUA/SINAICA
  (alcance de US-105).
- Avisar a Andrés González Habib (C3) que el esquema estrella completo ya tiene
  datos reales de D1-D4.

## Nota de transparencia (gobernanza del proyecto, regla 6)

Sesión de trabajo asistida por IA (Claude) para el diseño, redacción de SQL/YAML,
y validación end-to-end contra una base Postgres de prueba antes de aplicar los
cambios en mi máquina. Las decisiones de diseño (grano de `fact_escuela_ciclo`,
origen de `cve_mun` vía `dim_escuela`, manejo de SIN_DATO) están documentadas
inline en cada modelo.