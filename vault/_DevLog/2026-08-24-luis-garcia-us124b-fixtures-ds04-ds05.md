---
id: DEVLOG-2026-08-24-LUIS-US124B
title: "DevLog — US-124b: pruebas offline (pytest) para extractores y suites GE de DS-04/DS-05"
author: "Luis Enrique García Vázquez"
session_date: "2026-08-24"
ai_tool: "Claude Code (Sonnet 5)"
traces_up: ["US-124b", "REQ-001"]
affected_ids: ["US-124b", "TEST-010", "TEST-011", "REQ-001", "DS-04", "DS-05"]
tags: [devlog, ai-assisted, sprint-4, testing, sesnsp, sinaica, great-expectations]
---

# DevLog — US-124b: fixtures y pruebas offline de DS-04/DS-05

## Contexto

Última historia pendiente del bloque DS-04/DS-05. El texto original de `US-124b` pide "muestra
≤500 filas... para que CI corra sin descargar datos reales". Antes de escribir código revisé qué
ya existía en `tests/fixtures/` para no duplicar (regla del vault: "un tema, un archivo
canónico").

## Qué se pidió a la IA

> "Comenzar con la US-124b para generar los fixtures de DS-04 y DS-05."

## Qué hizo la IA (y qué se revisó)

### Investigación previa a escribir código

Encontró que ya existían `tests/fixtures/bronze_sesnsp_sample.csv` y
`bronze_sinaica_estaciones_sample.csv`/`bronze_sinaica_observaciones_sample.csv`, generados por
Diana el 18-19 de agosto. **Revisión mía:** inspeccioné el contenido antes de decidir qué hacer —
son fixtures **sintéticos a propósito** para probar su pipeline de Gold/IDW (`US-103/104/105`),
con `cve_ent`/`cve_mun` ya homologados a 2/5 dígitos (formato que Silver produce, no el que
Bronze recibe crudo) y estaciones colocadas en coordenadas específicas relativas a escuelas de
prueba. **Decisión mía:** no tocarlos ni reusar esos nombres — son de un tema distinto (Gold, no
Bronze/extractor), y modificarlos podría romper sus pruebas sin que yo tuviera visibilidad
completa de dónde más se usan.

También encontró `tests/test_extractor_formato911_historico.py` (escrito la semana pasada, mismo
estilo de la IA) como precedente reciente del repo: pruebas con datos sintéticos armados **inline**
vía el fixture `tmp_path` de pytest, no archivos CSV grandes committeados. Seguí ese mismo patrón
en vez de crear archivos nuevos en `tests/fixtures/` — evita cualquier colisión de nombres con los
de Diana y es consistente con lo más reciente del repo.

### Refactors para hacer el código testeable

- `extractor_sesnsp.py`: extraje `_derivar_cve_mun_local()` y `_finalizar_agregado()` como
  funciones puras (antes vivían inline dentro de `extraer_sesnsp()`).
- `extractor_sinaica.py`: extraje `_parsear_respuesta_datos()` y `_parsear_estaciones_activas()`
  del código que hace la llamada HTTP.
- `validacion_sesnsp.py`/`validacion_sinaica.py`: las funciones `validar_*` ahora aceptan `df` y
  `ge_context_dir` opcionales -- si no se pasan, el comportamiento normal (leer el Parquet más
  reciente de Bronze, usar `great_expectations/` real) no cambia.

**Revisión mía:** cada refactor se hizo primero, se corrió `pytest tests/ -q` completo (326
pruebas del repo, no solo las mías) para confirmar cero regresiones, y solo después se agregaron
los casos nuevos.

### Hallazgo real durante el trabajo: API deprecada de Great Expectations

Al escribir la prueba del rango físico por parámetro de SINAICA, `pytest` mostró ~400 warnings de
deprecación: `row_condition` como string + `condition_parser="pandas"` está deprecado desde GX
Core 1.9.0 y se elimina en 2.0. **No estaba buscando esto** -- lo encontré porque escribí la
prueba y until entonces el warning había pasado inadvertido en los runs manuales anteriores (no
usaban `-v` ni se leía la salida completa). Investigué la API nueva (`Column("parametro") ==
"O3"`, un objeto `Condition` en vez de un string) y migré `validacion_sinaica.py` antes de seguir
-- como `requirements.txt` fija `great-expectations>=0.18` sin techo, una futura resolución a GX
2.0 habría roto la suite en producción sin este cambio.

## Resultado

- **28 pruebas nuevas**, todas offline (sin red, sin `data/bronze/`, sin tocar el
  `great_expectations/` real): `test_extractor_sesnsp.py` (9), `test_extractor_sinaica.py` (7),
  `test_validacion_sesnsp.py` (4), `test_validacion_sinaica.py` (8).
- Cada prueba de las suites GE reproduce un hallazgo real ya documentado (conteo negativo,
  georreferencia con placeholder "0.0", tipo de delito fuera de catálogo, llave duplicada) para
  demostrar que la suite lo atrapa, no solo que corre sin tronar.
- `pytest tests/ -q` completo: **326 passed, 4 skipped** (los 4 `skipped` son preexistentes, no
  relacionados con este cambio).
- Se re-verificó la ruta real (CLI, no solo pruebas) contra los datos reales de Bronze después de
  la migración de API -- sin regresión.

## Decisiones tomadas (no delegadas a la IA)

1. **No crear archivos nuevos en `tests/fixtures/`** ni tocar los de Diana -- datos sintéticos
   inline en los propios archivos de prueba, siguiendo el precedente más reciente del repo.
2. **Migrar la API deprecada de Great Expectations ahora**, no dejarlo como deuda técnica, porque
   el pin abierto de `requirements.txt` (`>=0.18`) hace que una futura instalación limpia pudiera
   romperla sin aviso.
3. Exigir que `pytest tests/ -q` completo (no solo mis archivos nuevos) pasara en verde antes de
   dar el refactor por bueno.

## Archivos modificados

- `src/ingesta/extractor_sesnsp.py` — refactor para testabilidad (funciones puras extraídas).
- `src/ingesta/extractor_sinaica.py` — ídem.
- `src/ingesta/validacion_sesnsp.py` — parámetros `df`/`ge_context_dir` opcionales.
- `src/ingesta/validacion_sinaica.py` — ídem + migración de API `row_condition` deprecada.
- `tests/test_extractor_sesnsp.py`, `tests/test_extractor_sinaica.py`,
  `tests/test_validacion_sesnsp.py`, `tests/test_validacion_sinaica.py` (nuevos).
- `vault/06_Quality_Testing/Automated/Great_Expectations_DS05_Sinaica.md`,
  `Great_Expectations_DS04_Sesnsp.md` — sección de cobertura automatizada.
- `vault/12_Roadmap_Sprints/Sprints/1-luis-enrique-garcia-vazquez.md` — `US-124b` a Terminado.
- `vault/02_Requirements/Traceability_Matrix.md` — fila `REQ-001`.
- `vault/_DevLog/2026-08-24-luis-garcia-us124b-fixtures-ds04-ds05.md` (este archivo).
- `vault/_DevLog/_index.md` — nueva fila.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] No se suben datos reales pesados — todos los datos de prueba son sintéticos, inline
- [x] `ruff check` limpio, `pytest tests/ -q` completo en verde (326 passed, 4 skipped)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes

Ninguno.

## Próximos pasos

- Todas mis historias asignadas (`US-121b`–`US-124b`) quedan cerradas al 100%.
- Pendiente de otras células/PM: conectar las suites GE a un DAG/CI real (ya señalado en
  `TEST-010`/`TEST-011`), y avisar formalmente si algún workflow de `.github/` necesita el nuevo
  `requirements.txt` con `great-expectations` instalado (no lo agregué yo, ya estaba).
