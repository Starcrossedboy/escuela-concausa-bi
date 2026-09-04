---
id: DEVLOG-2026-09-02-LUIS-US122B-CARGADORES
title: "DevLog — Cargadores reales Bronze→Postgres para DS-04 y DS-05 (US-122b)"
author: "Luis Enrique García Vázquez"
session_date: "2026-09-02"
ai_tool: "Claude Code (Sonnet 5)"
traces_up: ["US-122b", "REQ-001"]
affected_ids: ["US-122b", "REQ-001", "DS-04", "DS-05"]
tags: [devlog, ai-assisted, sprint-4, sesnsp, sinaica, bronze, postgres]
---

# DevLog — Cargadores reales Bronze→Postgres para DS-04 y DS-05

## Contexto

`extractor_sesnsp.py` y `extractor_sinaica.py` ya descargan de las fuentes reales y escriben
Parquet a `data/bronze/` (prueba de descarga real completada el 2026-08-14 y 2026-08-24). Lo que
faltaba era el paso siguiente del contrato Bronze: cargar esos Parquet a `bronze.*` en Postgres,
mismo patrón que ya usan DS-06 (`cargar_bronze_conagua_real.py`) y DS-07
(`cargar_bronze_coneval_real.py`). Se preparó esta sesión para tener el cargador listo, sin
depender de que llegue nada adicional de la ruta crítica.

## Qué se pidió a la IA

> "Ayúdame a preparar los cargadores reales a Bronze para DS-04, DS-05 y DS-07 para tenerlos
> listos en cuanto lleguen las URLs de la ruta crítica."

## Fuera de alcance detectado antes de escribir código

DS-07 (CONEVAL) es de Deni Garrido Fragoso, no mío — mi Agent Context dice explícitamente "SOLO
tus fuentes DS-04 y DS-05" (US-121b). Antes de tocar nada verifiqué `cargar_bronze_coneval_real.py`
y la ficha `DS-07_CONEVAL_Rezago_Social.md`: ya existe cargador real completo, con datos reales
cargados y descarga auditada (SHA-256), estado `in_review` desde 2026-08-30. Se excluyó DS-07 de
esta sesión para no pisar el trabajo de Deni ni salirme de mi alcance (regla 9 del vault).

## Qué hizo la IA (y qué se revisó)

Antes de escribir código, se leyó el contrato completo ya existente para no inventar nombres de
tabla ni columnas:
- `dbt/models/sources.yml`: identifica `bronze.sesnsp`, `bronze.sinaica_estaciones`,
  `bronze.sinaica_observaciones` (hoy apuntando por default a los fixtures `*_test`).
- `dbt/models/silver/delitos_municipio.sql` y `aire_estacion.sql`: confirman las columnas exactas
  que Silver espera de cada fuente.
- `cargar_bronze_fixture.py`: DDL de referencia (`DDL_BRONZE_SESNSP`,
  `DDL_BRONZE_SINAICA_ESTACIONES/OBSERVACIONES`) usado hoy para los fixtures de CI.

Con eso, se escribieron dos cargadores nuevos siguiendo el mismo estilo que ya usaron Diana/Deni
para DS-06/DS-07 (inferencia de tipo Postgres desde el dtype real del Parquet, validación de
esquema existente, idempotencia por snapshot `_source`+`_ingested_at`, sin `DELETE`/`UPDATE`):

- **`src/ingesta/cargar_bronze_sesnsp_real.py`** — carga el Parquet más reciente de
  `data/bronze/sesnsp/` a `bronze.sesnsp`. Valida llave natural
  (`cve_ent, cve_mun, anio, mes, tipo_delito`) sin nulos ni duplicados antes de insertar.
- **`src/ingesta/cargar_bronze_sinaica_real.py`** — carga los dos productos que ya separa
  `extractor_sinaica.py` (`bronze.sinaica_estaciones`, `bronze.sinaica_observaciones`), con
  `--producto ambos|estaciones|observaciones`.

**Revisión mía:** compilé ambos con `py_compile` (sin Python en el PATH del shell del agente, usé
el intérprete del `.venv` del proyecto). Confirmé columna por columna contra
`delitos_municipio.sql`/`aire_estacion.sql` que los nombres que escribe cada cargador (heredados
tal cual del Parquet de cada extractor, sin renombrar) son los que Silver ya espera, para no
descubrir un desajuste hasta correr `dbt run`.

## Decisiones tomadas (no delegadas a la IA)

1. **Excluir DS-07 de esta sesión** — ver sección de alcance arriba.
2. **No correr Great Expectations dentro del cargador.** `validacion_sesnsp.py`/`validacion_sinaica.py`
   siguen siendo un paso separado; el cargador solo mueve el Parquet ya extraído a Postgres, igual
   que `cargar_bronze_conagua_real.py`.
3. **No tocar `dbt/models/sources.yml` todavía.** Los `var(...)` por defecto siguen apuntando a los
   fixtures `_test` — cambiarlos es una decisión de corte (cuándo Silver deja de leer fixture y
   pasa a leer la tabla real), no algo para decidir en silencio dentro de esta sesión. Queda anotado
   como pendiente en el docstring de cada script.
4. **No tocar `tests/**`.** Es alcance 🟡 (compartido); no agregué pruebas nuevas sin coordinar
   primero con el dueño del área.

## Archivos modificados

- `src/ingesta/cargar_bronze_sesnsp_real.py` (nuevo)
- `src/ingesta/cargar_bronze_sinaica_real.py` (nuevo)
- `vault/_DevLog/2026-09-02-luis-garcia-us122b-cargadores-bronze-real.md` (este archivo)
- `vault/_DevLog/_index.md` — nueva fila
- `vault/02_Requirements/Traceability_Matrix.md` — fila `REQ-001`

## Seguridad / calidad

- [x] Sin secretos hardcodeados (DSN de Postgres vía variables de entorno, mismo patrón que el
  resto de `src/ingesta/`)
- [x] Sin `DELETE`/`UPDATE`/`DROP` (solo `CREATE SCHEMA IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`
  e `INSERT`)
- [x] No se suben datos reales pesados (`data/bronze/` sigue gitignored)
- [x] `py_compile` limpio en ambos scripts
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes

Ninguno de código. Pendiente de decisión de corte (no bloqueante): cuándo actualizar los `var(...)`
de `sources.yml` para que Silver deje de leer los fixtures `_test` y lea `bronze.sesnsp` /
`bronze.sinaica_estaciones` / `bronze.sinaica_observaciones` reales.

## Próximos pasos

- Correr ambos cargadores contra Postgres real cuando se confirme el corte de datos a usar.
- Actualizar `bronze_sesnsp_identifier` / `bronze_sinaica_estaciones_identifier` /
  `bronze_sinaica_observaciones_identifier` en `sources.yml` (o pasarlos por `--vars`) una vez
  cargadas las tablas reales.
- Avisar a Diana (Tech Lead C1) del cambio de alcance (se excluyó DS-07) al abrir el PR.
