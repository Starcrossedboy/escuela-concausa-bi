---
project: "FARO"
date: "2026-08-30"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "~4h"
touches: ["DS-02", "BUG-034", "BUG-036"]
tags: [devlog, bronze, cct, ds02, prueba-descarga-real]
---

# DS-02 · SEP Catálogo CCT — carga real de producción

→ [[_DevLog/_index|Volver al índice]] · [[14_Data_Sources/DS-02_Catalogo_CCT]]

## Qué se hizo

**Contexto.** DS-02 es la llave primaria del proyecto (identidad + georreferencia de cada
escuela) y llevaba desde la Semana 1 con `status: draft`, URL `PENDIENTE-CONFIRMAR` y el
checklist de §9 100% sin marcar.

**Fuente localizada.** Portal oficial SIGED (`siged.sep.gob.mx/SIGED/datos_abiertos.html`),
sección "Descarga del Catálogo de Centros de Trabajo". Partido por rango de entidad (01-16 y
17-32) — de las 4 `SCOPE_ENTIDADES`, Nuevo León (19) cae en el segundo archivo.

**Inspección real.** Ambos CSV descargados (250.6 MB + 196.4 MB, 597,685 filas crudas):
encoding Latin-1 (no UTF-8), 92 columnas propias de SIGED. **Hallazgo corregido en vivo:**
`C_TIPO=="ESCUELA"` **no** implica educación básica (también incluye media superior, superior,
inicial, CAM y formación para el trabajo) — el filtro real de básica es
`TIPONIVELSUB_C_SERVICION2` (*sic*, typo real del archivo) en
`{PREESCOLAR, PRIMARIA, SECUNDARIA}`, confirmado contra el fixture real de DS-01.
`INMUEBLE_CV_MUN` es el código local de 3 dígitos, no la clave INEGI de 5 —
`normalize_cve_mun()` ya sabe concatenar.

**Extractor/cargador.** `src/ingesta/cargar_bronze_cct_real.py`, mismo patrón que
`cargar_bronze_formato911_real.py`. Carga a `bronze.cct_siged_202608` reusando
`cargar_fixture()` (esquema `"cct"`). `dbt/models/sources.yml`: default de
`bronze_cct_identifier` de `cct_sample` a `cct_siged_202608`.

**BUG-034 (corregido en esta rama).** El diccionario ya anticipaba coordenadas erróneas; 6 de
77,712 escuelas de básica en las 4 `SCOPE_ENTIDADES` traían `latitud`/`longitud` en `0.0`, y
`silver/escuela.sql` solo nulificaba cadenas vacías, nunca ceros literales — esas 6 escuelas
pasaban con georreferencia "válida" a la interpolación IDW de D5/D6 (ADR-006). Fix:
`nullif(nullif(..., '')::double precision, 0)` sobre `latitud`/`longitud`, con guarda de
regresión `dbt/tests/valid_escuela_georreferencia.sql`.

**BUG-036 (corregido en esta rama, código compartido).** Al cargar las 385,175 filas reales,
`cargar_fixture()` reportó "75 insertadas" — falso, confirmado con un `COUNT(*)` directo en
Postgres (385,175 reales). Causa: `cur.rowcount` después de `execute_values()` solo refleja el
último lote interno (`page_size=100` por default): `385175 % 100 = 75`. Afecta a todos los
cargadores reales del proyecto con más de 100 filas — los datos siempre quedaron completos
(`ON CONFLICT DO NOTHING` funciona bien), solo el conteo impreso mentía. Fix: `RETURNING` +
`execute_values(..., fetch=True)`, que sí agrega los resultados de todas las páginas.

**Resultado real, de punta a punta (verificado en Postgres, no estimado):**
- `bronze.cct_siged_202608`: 385,175 filas (nacional, `01-16`: 217,224 + `17-32`: 167,951)
- `silver.escuela`: 385,175 filas
- `gold.dim_escuela`: **77,712** — coincide exacto con el conteo manual verificado al inicio de
  la sesión (CDMX 13,495 · Jalisco 21,532 · Edomex 32,423 · Nuevo León 10,262)

## Cómo se probó

pytest tests/test_cargar_bronze_cct_real.py -q          → 9 passed
pytest tests/test_cargar_bronze_fixture_conteo.py -q     → 2 passed
pytest tests/ -q                                          → 654 passed, 5 skipped

dbt run --select escuela+ --full-refresh
  → PASS=12 ERROR=1 (el error es cubo_pipeline, hueco preexistente de DS-06/silver.agua_region,
    no relacionado)

dbt test --select escuela
  → 6 passed, 1 error (mismo hueco preexistente de DS-06)
  → valid_escuela_georreferencia (guarda de BUG-034) PASS contra datos reales
  → not_null_escuela_cct/cve_ent/cve_mun, unique_escuela_cct, valid_escuela_keys: PASS

Carga real ejecutada contra Postgres local (`docker compose up -d db`), con las dos partes del
catálogo ya descargadas por Diana Alvarez Varela.

## Archivos tocados

- `src/ingesta/cargar_bronze_cct_real.py` (nuevo)
- `tests/test_cargar_bronze_cct_real.py` (nuevo)
- `tests/test_cargar_bronze_fixture_conteo.py` (nuevo, BUG-036)
- `dbt/models/sources.yml` (default de `bronze_cct_identifier`)
- `dbt/models/silver/escuela.sql` (BUG-034)
- `dbt/tests/valid_escuela_georreferencia.sql` (nuevo, BUG-034)
- `src/ingesta/cargar_bronze_fixture.py` (BUG-036)
- `14_Data_Sources/DS-02_Catalogo_CCT.md` (§2, §5, §9, §10 — `status: draft` → `in_review`)
- `06_Quality_Testing/Bug_Register.md` (BUG-034 y BUG-036 → `fixed`)

## Pendiente

- Materializar los cubos Gold en Cloud SQL (prod) — fuera de alcance de esta rama, es el
  desbloqueo de Fase 3 que pidió Luis Téllez.
- Suite de Great Expectations para DS-02 (y DS-01) — señalado por Deni Garrido en su auditoría
  del 30-ago, todavía no existe.
- BUG-035 (housekeeping: tablas `*_sample`/`*_test` huérfanas en `bronze`) — encontrado en esta
  sesión, registro pendiente, en pausa por decisión de Diana.