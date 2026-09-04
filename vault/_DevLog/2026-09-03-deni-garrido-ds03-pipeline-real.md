---
project: "FARO"
date: "2026-09-03"
author_human: "Deni Garrido Fragoso"
agent: "OpenCode"
model: "GPT-5.6 Sol"
session_duration: "desbloqueo de DS-03 para Carril A"
touches: ["DS-03", "REQ-001"]
tags: [devlog, data-source, cemabe, bronze, pipeline-real]
---

# DS-03 — descarga, parser y cargador reales de CEMABE

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/14_Data_Sources/DS-03_CEMABE]]

## Objetivo

Entregar la URL oficial y una muestra real de CEMABE, y convertir esa evidencia en una ruta
reproducible hasta `bronze.cemabe_2013` para retirar el bloqueo de DS-03 en el Carril A.

## Resultado

- Se confirmaron los endpoints oficiales SEP-SIGED de `INMUEBLE_CSV.zip` (`idFile=343`) y
  `CENTRAB_CSV.zip` (`idFile=352`).
- Se generaron muestras reales de cinco filas de ambos CSV bajo `data/raw/cemabe/muestra/` con
  las columnas físicas que consume el parser. No se versionan porque el protocolo prohíbe subir
  datos reales; la ficha conserva el esquema, los conteos y las rutas locales de evidencia.
- `extractor_cemabe.py` descarga y valida los dos ZIP, los une por `ID_INM`, transforma los seis
  indicadores requeridos y genera una fila por CCT en Parquet.
- `cargar_bronze_cemabe_real.py` carga ese Parquet de forma idempotente en
  `bronze.cemabe_2013`.
- `dag_censal_estatico.py` encadena extracción y carga.

## Hallazgo de esquema

`CENTRAB.CLAVE_CT` no es el CCT canónico de 10 caracteres: el diccionario oficial lo define como
**CCT + turno**, con longitud 11. El parser retira el último carácter y consolida los turnos por
CCT. Esta regla evita que `normalize_cct` convierta todos los registros reales en nulos.

La corrida encontró 68 claves temporales que no cumplen el patrón oficial, por ejemplo
`27DJNTEMP31`. Se excluyen explícitamente; no se inventa una equivalencia.

## Evidencia real

- `INMUEBLE_CSV.csv`: 166,138 filas y 162 columnas.
- `CENTRAB_CSV.csv`: 205,912 filas y 202 columnas.
- Parquet conformado: **203,570 CCT únicos**, todos de longitud 10 y sin duplicados.
- Carga PostgreSQL: **203,570/203,570 filas insertadas** en `bronze.cemabe_2013`.
- Se retiraron exactamente 72 filas del fixture sintético previo, identificadas por
  `_source_url=https://www.inegi.org.mx/programas/cemabe/2013/`.
- `silver.cemabe`: **203,570 filas reales** después de reconstruir el modelo.
- Catálogos de los seis drivers: exclusivamente `1`, `0` o vacío; Silver convierte vacío a
  `SIN_DATO`.

## Validaciones

- Extracción completa contra SEP-SIGED: PASS.
- Conformación de las muestras versionadas: PASS.
- Inspección del Parquet: 203,570 filas, 203,570 CCT únicos, 0 duplicados: PASS.
- `ruff check` sobre extractor, cargador y DAG: PASS.
- `py_compile` sobre extractor, cargador y DAG: PASS.
- `pytest tests/test_extractor_cemabe.py -q`: 2/2 PASS; cubre mapeo físico, CCT + turno,
  consolidación de turnos y exclusión de claves temporales con datos sintéticos.
- `pytest tests/ -q`: 780 PASS, 5 skipped; una advertencia ambiental de deprecación Starlette.
- `dbt parse --no-partial-parse`: PASS; una deprecación preexistente en
  `models/silver/schema.yml`.
- `dbt build --select cemabe --exclude cubo_pipeline_rows_parity`: **9/9 PASS** (un modelo y
  ocho pruebas propias). El test excluido requiere `gold.cubo_pipeline`, que no está
  materializado en este entorno y no forma parte de la validación propia de DS-03.
- `git diff --check`: PASS.

## Dependencia operativa

La API de SIGED requiere el almacén TLS del sistema en este entorno. Se validó con
`truststore==0.10.4`, dependencia que Diana ya agregó en `origin/dev/diana-alvarez`; este cambio
debe llegar a `main` antes de ejecutar el extractor desde un ambiente limpio.
