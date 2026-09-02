---
id: DEVLOG-2026-08-18-LUIS-US122B
title: "DevLog — US-122b Extractor real de DS-05 (SINAICA) + respuesta a Diana sobre DS-04"
author: "Luis Enrique García Vázquez"
session_date: "2026-08-18"
ai_tool: "Claude Code (Sonnet 5)"
traces_up: ["US-122b", "US-121b", "REQ-001"]
affected_ids: ["US-122b", "US-121b", "REQ-001", "DS-05", "DS-04"]
tags: [devlog, ai-assisted, sprint-2, sprint-3, bronze, sinaica]
---

# DevLog — US-122b: extractor real de DS-05 (SINAICA)

## Contexto

Retomé el trabajo tras el bloqueo de `US-121b` en DS-04. Diana (Tech Lead) había comentado el PR
#31 el 15-ago pidiendo el link exacto del recurso bloqueado y si había endpoints alternos para
SESNSP. Antes de programar, respondí eso, y luego arranqué `US-122b` (extractores idempotentes a
Bronze) empezando por DS-05, que ya no tiene bloqueos.

## Qué se pidió a la IA

> "Publica el comentario en el PR #31 para Diana y haz el commit y PR de la parte de DS-05 para
> la US-122b."

(En el turno anterior ya se había redactado la respuesta a Diana y el extractor, con revisión mía
antes de publicar/commitear.)

## Qué hizo la IA (y qué se revisó)

### Respuesta a Diana (PR #31)

Redactó y (tras mi confirmación explícita) publicó un comentario con: el link exacto del ZIP
bloqueado (`Municipal-Delitos-2015-2025_jun2026.zip` vía SharePoint), confirmación de que
`&download=1` no evita el login de Microsoft, y las dos alternativas que ya se habían probado
(`datos.gob.mx` API CKAN → 403 Akamai; `secretariadoejecutivo.gob.mx` → no se pudo conectar, sin
poder distinguir si es la misma protección u otra causa). **Revisión mía:** confirmé que los datos
técnicos citados coinciden con lo ya documentado en `DS-04_SESNSP_Incidencia_Delictiva.md` antes
de autorizar la publicación.

### Extractor real de DS-05 (`src/ingesta/extractor_sinaica.py`)

Reemplazó el placeholder genérico que Diana había dejado como scaffolding (US-102, apuntaba solo a
la home de SINAICA y usaba `response.json()`, que no funciona contra la respuesta real) por una
implementación real con dos funciones:

- `extraer_sinaica_estaciones()` — catálogo de estaciones vía `getData.php`.
- `extraer_sinaica_observaciones()` — lecturas horarias vía `datGrafs.php`, con extracción por
  regex del `var dat = [...]` embebido (la respuesta no es JSON puro) y manejo defensivo por
  estación/parámetro (si una estación no reporta un parámetro, se registra el aviso y se sigue,
  sin tumbar la corrida completa).
- `extraer_sinaica()` — wrapper que corre ambas; mantiene el mismo nombre que ya importa
  `dags/dag_horario.py`, así que **no hizo falta tocar el DAG**.

Produce las dos tablas Bronze (`sinaica_estaciones`, `sinaica_observaciones`) que ya esperaba
`dbt/models/silver/aire_estacion.sql` (escrito antes por Deni en US-111), con `_ingested_at`,
`_source`, `_source_url` en ambas.

**Revisión y prueba real (no simulada):**
- Se creó un `.venv` con `pandas`, `pyarrow`, `requests` y se corrió el extractor contra la API
  real de SINAICA (no un mock): **384 estaciones** descargadas y **34 registros horarios reales
  de hoy** (PM2.5/O3, estación 33 "Centro", Aguascalientes).
- Se inspeccionaron a mano las columnas y una muestra de filas del Parquet resultante para
  confirmar que el esquema coincide con lo que espera el modelo Silver.
- `ruff check` y `py_compile` limpios.
- Los Parquet de prueba quedaron en `data/bronze/sinaica/...`, que ya está en `.gitignore` — no se
  sube nada de eso al repo.

## Decisiones tomadas (no delegadas a la IA)

1. Autoricé publicar el comentario a Diana solo después de revisar que el contenido técnico fuera
   exacto (no delegué esa verificación).
2. Decidí avanzar `US-122b` solo para DS-05 en este PR, dejando DS-04 fuera hasta que Diana
   resuelva el acceso — evita mezclar código que funciona con código que seguiría bloqueado.
3. Acepté mantener el nombre `extraer_sinaica()` como wrapper para no tener que tocar
   `dags/dag_horario.py`, en vez de partir en dos tareas de Airflow (más "correcto"
   arquitectónicamente, pero fuera del alcance de esta historia).

## Archivos modificados

- `src/ingesta/extractor_sinaica.py` — extractor real (reemplaza el placeholder de Diana).
- `vault/12_Roadmap_Sprints/Sprints/1-luis-enrique-garcia-vazquez.md` — tabla de seguimiento.
- `vault/02_Requirements/Traceability_Matrix.md` — fila `REQ-001`, columna DevLog.
- `vault/_DevLog/2026-08-18-luis-garcia-us122b-extractor-sinaica.md` (este archivo).
- `vault/_DevLog/_index.md` — nueva fila.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] No se suben datos reales pesados (Parquet de prueba quedan en `data/bronze/`, gitignored)
- [x] `ruff check` limpio, `py_compile` limpio
- [x] DevLog enlaza a los IDs afectados (`US-122b`, `US-121b`, `REQ-001`, `DS-05`, `DS-04`)

## Bloqueantes

- DS-04 sigue bloqueada (login de Microsoft/SharePoint). Ya se le pasó a Diana el link exacto y
  las alternativas descartadas; queda pendiente su respuesta para poder avanzar el extractor de
  DS-04.

## Próximos pasos

- Cuando Diana resuelva DS-04, escribir `extraer_sesnsp()` real y cerrar `US-122b` por completo.
- Empezar `US-123b` (Great Expectations) para DS-05, que ya tiene datos reales en Bronze para
  validar contra.
