---
project: "FARO"
date: "2026-08-28"
author_human: "Emilio Galnares Ruiz"
agent: "Claude"
model: "claude-sonnet"
session_duration: "varias sesiones (28 ago)"
touches: ["US-121a", "US-122a", "US-123a", "US-124a"]
tags: [devlog]
---

# DevLog — 2026-08-28 — Prueba de descarga, extractores y validaciones DS-06/DS-08

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo
- Se identificó y probó la accesibilidad real de DS-06 (CONAGUA) y DS-08 (CONAPO).
- Para DS-06, el catálogo estático de datos.gob.mx (210 registros) no traía datos
  volumétricos; se ubicó una fuente alterna con datos reales (IMTA/SISUAR,
  `https://sisuar.imta.mx/aplicacion/vista/presa/presas.php`), confirmada como
  serie histórica por presa (no un valor fijo).
- Se descubrió, inspeccionando el tráfico de red del navegador (pestaña Network de
  DevTools), que el formulario web de esa página envía internamente una petición
  **POST** al endpoint `https://sisuar.imta.mx/aplicacion/controlador/mapa.php`
  con dos parámetros: `Accion=Presas` y `query=(id_estado=1 or id_estado=2 or ...)`.
  Al seleccionar todos los estados en el formulario, el `query` arma automáticamente
  la condición completa con los 33 códigos — se replicó ese mismo patrón en Python
  con `requests.post`, evitando así un loop estado-por-estado y trayendo las 180
  presas en una sola llamada.
- Para DS-08, se confirmó que CONAPO no ofrece URL de descarga permanente (la app
  de descarga usa sesiones temporales tipo Shiny/RStudio); se optó por partir del
  archivo descargado manualmente (`pobproy_quinq1.csv`, 252,450 filas) en vez de
  automatizar la descarga.
- Se corrigió la clave de municipio de DS-08 (columna `CLAVE`, venía como entero
  sin ceros a la izquierda) con `.astype(str).str.zfill(5)`.
- Se construyeron y probaron ambos extractores, guardando en Bronze con las
  columnas `_ingested_at`, `_source`, `_source_url`.
- Se armaron suites de Great Expectations para ambas fuentes (7 expectativas cada
  una: nulos, unicidad de llave, rangos físicos, formato) — 7/7 exitosas en ambas.
- Se generaron fixtures de prueba para CI (180 filas DS-06, muestra de 500 filas
  de DS-08).
- Tras revisión de PR, se fusionó la lógica en los archivos canónicos que Diana
  Álvarez Varela ya había preparado en `src/ingesta/extractor_conagua.py` y
  `extractor_conapo.py` (reemplazando el placeholder `SOURCE_URL =
  "PENDIENTE-CONFIRMAR"`), y se reubicaron validaciones y fixtures siguiendo la
  convención de nombres del equipo.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude (asistencia conversacional paso a paso, usuario sin
  experiencia previa en programación/Git).
- **Archivos creados/modificados:**
  - `src/ingesta/extractor_conagua.py` (lógica real reemplazando placeholder)
  - `src/ingesta/extractor_conapo.py` (lógica real reemplazando placeholder)
  - `src/ingesta/validacion_conagua.py` (suite Great Expectations DS-06)
  - `src/ingesta/validacion_conapo.py` (suite Great Expectations DS-08)
  - `tests/fixtures/generate_bronze_conagua_conapo_fixtures.py`
  - `tests/fixtures/bronze_ds06_conagua_sample.csv`
  - `tests/fixtures/bronze_ds08_conapo_sample.csv`
  - `great_expectations/expectations/suite_ds06_conagua.json`
  - `great_expectations/expectations/suite_ds08_conapo.json`
  - `vault/14_Data_Sources/DS-06_CONAGUA_SINA.md` (fichas actualizadas)
  - `vault/14_Data_Sources/DS-08_CONAPO_Proyecciones.md` (fichas actualizadas)
- **Decisiones autónomas del agente:** propuso el flujo Fork + upstream remote al
  detectar que el proyecto usa branch protection; sugirió alinear nombres de
  archivos con la convención del equipo (`great_expectations/`, `suite_*.json`,
  `bronze_*_sample.csv`) antes de abrir el PR, tras detectar la duplicidad al
  traer los commits de `main`.
- **Correcciones manuales:** el usuario corrigió manualmente los nombres de
  archivo cuando VS Code abría pestañas equivocadas; validó cada resultado de
  terminal antes de continuar al siguiente paso.
- **Prompt inicial:** guía paso a paso para configurar el ambiente local
  (Python, Git, Docker) y avanzar la historia US-121a sin experiencia previa en
  programación.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Tests agregados/actualizados (suites Great Expectations DS-06 y DS-08, 7/7
      exitosas cada una; fixtures para CI)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- DS-06 vía IMTA/SISUAR no tiene documentación pública del endpoint `mapa.php`;
  si la estructura del formulario cambia, el `payload` (`query`, `Accion`) tendría
  que volver a capturarse con DevTools.
- Falta cargar el dato a Postgres y actualizar `dbt/models/sources.yml` (default
  `conagua_no_ingerido` → nombre real de la tabla) para que el driver D5 se
  encienda en los tableros — coordinar con Diana y Deni.

## Próximos pasos
- Agregar `tests/test_extractor_ds06.py` y `tests/test_validacion_ds06.py`
  siguiendo el patrón de DS-04/DS-05 (pendiente de esta misma sesión).
- Actualizar `vault/02_Requirements/Traceability_Matrix.md`, renglón REQ-001.
- Coordinar con Diana/Deni la carga a Postgres y el ajuste de `sources.yml`.