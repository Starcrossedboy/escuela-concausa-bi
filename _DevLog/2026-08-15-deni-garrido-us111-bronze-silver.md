---
project: "FARO"
date: "2026-08-15"
title: "US-111 · Implementación Bronze a Silver con dbt"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
session_duration: "avance parcial"
touches: ["US-111", "REQ-001", "DS-01", "DS-02", "DS-03"]
tags: [devlog, ai-assisted, sprint-2, celula-1, dbt, silver]
---

# DevLog — 2026-08-15 — US-111 Bronze → Silver con dbt

> [[_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se retomó `US-111` en la rama `feat/deni-fragoso-us-111`.
- Se validó el alcance contra `REQ-001`, `03_Architecture/Data_Model.md`, contratos de fuentes y contexto de agente.
- Se confirmó el stack local `dbt-postgres` + PostgreSQL.
- Se levantó y validó PostgreSQL local (`escuela_concausa_db`).
- Se creó la estructura inicial del proyecto dbt en `dbt/`.
- Se configuró la conexión local de dbt fuera del repositorio mediante `~/.dbt/profiles.yml`.
- Se validó la conexión con `dbt debug`.
- Se implementaron macros de homologación para:
  - CCT a 10 caracteres.
  - clave INEGI de entidad a 2 dígitos.
  - clave INEGI municipal a 5 dígitos.
  - drivers binarios con política explícita `SIN_DATO`.
- Se declararon sources Bronze para DS-01, DS-02 y DS-03.
- Se implementó `silver.matricula`:
  - tipado explícito;
  - homologación de llaves;
  - deduplicación por `cct + ciclo`;
  - conservación de la ingesta más reciente;
  - metadatos de linaje.
- Se implementó `silver.escuela`:
  - tipado;
  - homologación CCT/INEGI;
  - deduplicación por CCT;
  - conservación de metadatos Bronze.
- Se agregaron tests dbt para `not_null`, unicidad y formato de llaves.
- Se validaron los modelos y tests mediante `dbt parse` y `dbt compile`.
- Se inició el análisis del contrato DS-03 CEMABE para continuar con `silver.cemabe`.

## Sesión de IA

- **Agente / modelo:** ChatGPT / GPT-5.6 Sol
- **Archivos creados/modificados:**
  - `dbt/dbt_project.yml`
  - `dbt/macros/normalize_binary_driver.sql`
  - `dbt/macros/normalize_cct.sql`
  - `dbt/macros/normalize_cve_ent.sql`
  - `dbt/macros/normalize_cve_mun.sql`
  - `dbt/models/sources.yml`
  - `dbt/models/silver/matricula.sql`
  - `dbt/models/silver/escuela.sql`
  - `dbt/models/silver/schema.yml`
  - `dbt/tests/unique_matricula_cct_ciclo.sql`
  - `dbt/tests/valid_matricula_keys.sql`
  - `dbt/tests/valid_escuela_keys.sql`
- **Decisiones:** Bronze y Silver se mantienen nacionales; no se filtra por `SCOPE_ENTIDADES` en esta capa. Las llaves inválidas no se corrigen silenciosamente. `SIN_DATO` se conserva como categoría explícita para ausencia de cobertura.
- **Correcciones manuales:** se revisaron comandos y SQL compilado antes de continuar; se evitó introducir una política global de schemas que pudiera afectar a otros integrantes del equipo.
- **Commit de avance:** `257b58` — `feat(dbt): avance US-111 Bronze a Silver`

## Seguridad / calidad

- [x] Sin secretos ni credenciales versionados.
- [x] `profiles.yml` permanece fuera del repositorio.
- [x] `dbt debug` con conexión PostgreSQL exitosa.
- [x] `dbt parse` ejecutado sin errores sobre el trabajo implementado.
- [x] `dbt compile` ejecutado sobre los modelos y tests desarrollados.
- [x] Bronze/Silver conservan alcance nacional.
- [x] Homologación de CCT e INEGI alineada con `Data_Model.md`.
- [ ] Ejecución end-to-end contra Bronze real pendiente.
- [ ] `vault_lint.py` pendiente al cierre de US-111.

## Bloqueantes / dependencias

- Los datos Bronze reales no se versionan en Git.
- La instancia PostgreSQL local validada no contenía todavía tablas Bronze materializadas.
- DS-02 todavía no tiene un identificador físico Bronze confirmado; en compilación se utilizó un valor temporal únicamente para resolver el source.
- La prueba de descarga real de DS-03 CEMABE sigue pendiente según su contrato.
- Estos puntos no bloquean el desarrollo del contrato/modelos dbt, pero sí la validación end-to-end con datos reales.

## Próximos pasos

- Implementar `silver.cemabe` respetando el contrato DS-03 y la política `SIN_DATO`.
- Continuar con los modelos Silver restantes definidos en `03_Architecture/Data_Model.md`.
- Ejecutar una validación global evitando repetir controles ya aprobados.
- Validar contra Bronze real cuando esté disponible.
- Actualizar trazabilidad y estado de `US-111`.
- Ejecutar `vault_lint.py`.
- Completar revisión Git, push y PR para revisión del Tech Lead.
