---
project: "FARO"
date: "2026-08-21"
author_human: "Manuel Alejandro Serrania Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
session_duration: "construcción de US-203: datasets, métricas, tableros DB-01/DB-02 en Superset 6.1, mock ML, GeoJSON municipal y fix del driver Postgres"
touches: ["US-203", "REQ-002", "KPI-01", "KPI-02", "KPI-03", "KPI-04", "KPI-05", "KPI-07", "KPI-08", "KPI-09", "KPI-10", "DOC-SCREENSPECS", "DEC-005", "DEC-008"]
tags: [devlog, bi, superset, dashboards, mock, geojson, celula-2]
---

# DevLog — 2026-08-21 — US-203: DB-01 Ejecutivo y DB-02 Mapa de riesgo en Superset

→ [[_DevLog/_index|Volver al índice]] · [[04_UX_Design/Screen_Specs]] · [[03_Architecture/Data_Model]]

## Contexto
US-203 construye los dos primeros tableros sobre la convención de US-202 y el patrón DEC-008 fijado por
US-211a. **US-212 sigue bloqueada por US-113** (los cubos `gold.cubo_*` no existen), así que los datasets
son **SQL virtual autocontenido** que sirve doble propósito: dataset de Superset hoy y SQL de referencia
para la materialización de C1 mañana (mismo trato que US-211a). Las salidas de ML-01/ML-02 tampoco han
llegado (US-311/313, BLOCK de calendario): se trabajó contra **mock local** según el plan de sprint.

## Qué se hizo

### Capa semántica (`superset/semantic/`)
- **`db01_cubo_matricula.sql`** — grano `cve_mun × nivel × ciclo`; componentes aditivos
  (`variacion_x_matricula`, `suma_completitud`), sin promedios precalculados.
- **`db02_cubo_riesgo_territorial.sql`** — riesgo por **LEFT JOIN** a `gold.predicciones`
  (`cct + id_ciclo + modelo='ML-01'`); `escuelas_con_prediccion` como denominador real;
  bandera `cobertura_riesgo = 'SIN_DATO'`.
- **`db01_distribucion_escuelas.sql`** (KPI-08/09) y **`db01_driver_dominante.sql`** (KPI-07,
  LEFT JOIN a `gold.recomendaciones`, etiqueta SIN_DATO para escuelas aún no explicadas).
- **`db02_puntos_escuela.sql`** — capa scatter al grano cct × ciclo con lat/long y riesgo.
- **`db02_coropletico.sql`** — cubo + geometrías; **sin `nivel` en el grano a propósito**
  (nivel duplicaría polígonos superpuestos).
- **`metrics_db01_db02.yaml`** — 6 datasets, 3 filtros globales, razones como SUM/SUM con NULLIF,
  `% en riesgo` divide entre escuelas puntuadas (no inventa cobertura).

### Tableros declarativos (`superset/dashboards/`) + sync extendido
- `db01_ejecutivo.yaml` (9 charts: 4 tiles KPI, serie temporal, ranking, 2 pies, drivers) y
  `db02_mapa_riesgo.yaml` (7 charts: tiles KPI-03/04, coroplético deck_polygon, puntos deck_scatter,
  ranking).
- `sync_semantic_layer.py` extendido (idempotente): crea charts por REST, arma layout v2, registra
  filtros nativos y valida cada chart contra datos (`--validar-datos`).
- **Compatibilidad Superset 6.1 (3 hallazgos depurados contra la API real):**
  1. Los tipos de filtro nativo ya no son `native_filters.SelectFilter` sino
     `filter_select` / `filter_range` / … (enum `FilterPlugins` del frontend); con la llave vieja el
     tablero renderiza "Item with key … is not registered".
  2. El PUT REST de dashboards **no asocia charts** (`dashboard_slices` solo lo llena el flujo de
     importación v1): sin eso el tablero muestra "no chart definition associated". La vía canónica es
     `POST /api/v1/dashboard/import/` con un ZIP (`metadata.yaml` + `databases|datasets|charts|
     dashboards/*.yaml`, todo bajo una carpeta raíz y cada YAML como un único mapeo). El script arma
     ese bundle en memoria: targets de filtros van planos con `datasetUuid` y el importador los
     remapea a `datasetId`; los CHART del layout llevan `meta.uuid`.
  3. Rate limit 50 req/s: `_request` reintenta ante 429; detalle de BD cacheado por corrida.
- Resultado verificado por API: **DB-01 id=1 (9 charts + filtros ciclo/entidad/nivel)** y
  **DB-02 id=2 (7 charts + filtros ciclo/nivel)**, ambos publicados en `127.0.0.1:8088`,
  asociados vía `dashboard_slices`, sin duplicados y con segunda corrida sin creaciones.

### Mock local de ML (`superset/mock/gold_ml_outputs_mock.sql`)
- Determinístico por hash del CCT (screenshots reproducibles), marcado `mlflow_run_id='MOCK-US203'`,
  idempotente (`ON CONFLICT DO NOTHING`), sin DDL destructivo (único ALTER aditivo para completar
  DEC-005 si la tabla local quedó mínima).
- Siembra el catálogo `dim_driver` D1–D6 (el local solo tenía D1; sin eso KPI-07 colapsaba en SIN_DATO)
  y deja un municipio completo sin predicciones para ejercitar SIN_DATO end-to-end.
- Guardarraíles en tests: identificable, idempotente, no destructivo, solo toca tablas de salida ML.

### GeoJSON municipal (`superset/assets/geojson/`)
- Confirmado con Manuel: espejo comunitario INEGI/CONABIO 2023 (MIT) + commit del asset filtrado.
- `generar_geojson_municipios.py` filtra SCOPE_ENTIDADES (317 municipios) y simplifica
  (Douglas-Peucker ~200 m) hasta **606 KB**; llave `cve_mun` CVEGEO 5 dígitos.
- `cargar_geojson_municipios.py` → `gold.geo_municipio` (tabla local, idempotente).

### 🐛 Fix de ambiente necesario para validar (revisar con C5)
- **`docker/superset.Dockerfile`: `pip install psycopg2-binary` instalaba en el Python del sistema,
  pero Superset corre en `/app/.venv` gestionado con `uv`** → "No module named 'psycopg2'" al crear
  cualquier dataset (bug latente: la conexión nunca funcionó). Corregido a
  `uv pip install --python /app/.venv/bin/python`. Es archivo del stack Superset, no tocó
  docker-compose ni .gitattributes; se señala para revisión de C5.

## Datos locales usados
Fixtures bronze sintéticos → dbt 12/12 modelos OK (fact 25, dims 60/10/2), 91 data tests OK.
Vars de identificadores pasadas por `--vars` (convención pendiente de documentar en Environment_Setup).

## Verificación
- `pytest tests/test_semantic_db01_db02.py -q` → **47 passed** (R1/R2/R3, grano, YAML, tableros, mock, sync).
- Suite completa: **256 passed, 4 skipped** (baseline de Marina restaurada tras re-sincronizar el venv
  con `requirements.txt`, que quedó mínimo sin jose/sklearn).
- `ruff check` limpio en los 4 archivos Python del cambio.
- `sync_semantic_layer.py --validar-datos` → 16/16 charts con datos; ranking 9 municipios,
  drivers 7 categorías (D1..D6 + SIN_DATO), puntos 23/25 (2 sin coordenadas, correcto).
- Ambos dashboards inspeccionados por API tras importación v1: layout con `meta.uuid`,
  `dashboard_slices` poblado (9+7), filtros `filter_select` con datasetIds remapeados.
- Idempotencia: segunda corrida sin crear objetos y sin duplicados en datasets/dashboards/charts.

## Verificación E2E con Playwright (2026-08-22, segunda sesión)
Tras la revisión de Manuel (tiles vacíos/texto cortado), se instrumentó el tablero real con Playwright
(Chromium headless, login por UI, lectura de DOM + consola + red). Tres bugs reales encontrados y
corregidos — **todos eran del script de sync, no de Superset**:

1. **`% escuelas en riesgo` mostraba 3,181.8%** — doble escalado: la expresión SQL multiplicaba ×100
   Y el formato d3 `,.1%` vuelve a multiplicar. Fix: el YAML guarda la razón pura (0.318) y el único
   mapa de formatos (`FORMATO_D3`) usa sufijo `%`. Se eliminó `_FORMAT_MAP` (dos mapas divergentes
   fue la causa raíz).
2. **Métricas de dataset nunca se actualizaban** — `_apply_metrics_and_columns` se saltaba las métricas
   existentes ("ya existe") y mandaba el formato en `extra.d3Format`, campo inexistente (el schema es
   `d3format`). Además el PUT distingue update de alta por la presencia de `id` numérico
   (`_validate_metrics`): sin id trata la entrada como nueva y rechaza 422 "already exist". Fix:
   lista completa con `id`/`uuid` de existentes + campo `d3format`.
3. **Scatter deck.gl sin puntos** — las claves del bloque `spatial` son `lonCol`/`latCol`, no
   `longitudeCol`/`latitudeCol` (verificado contra el bundle compilado).

4. **La barra de filtros nativos no se montaba** — el más difícil. El enum del frontend es
   `FilterBarOrientation.Vertical = 'VERTICAL'` (MAYÚSCULAS); nuestro `json_metadata` escribía
   `"filter_bar_orientation": "vertical"` y ninguna comparación del DashboardBuilder hacía match,
   así que ni la barra vertical ni la horizontal se montaban (sin errores de consola: falla silenciosa).
   Diagnosticado leyendo Redux desde el fiber de React vía Playwright (`dash_edit_perm=true`,
   `nfc_len=3`, orientación correcta → el estado estaba bien, el gate era el string). Fix:
   `"VERTICAL"`. Nota: cuando la llave NO existe, el default del hydrate sí funciona — por eso antes
   de escribir esa llave la barra montaba (y ahí salía el toast del hallazgo 1 de la sesión anterior).

Verificación final (Playwright + API):
- **DB-01**: 9/9 charts renderizan (4 tiles con valores, serie con canvas, tabla 9 filas, 3 pies).
- **DB-02**: 7/7 charts renderizan; coroplético con leyenda de rangos, scatter con canvas,
  ranking muestra N/A para el municipio SIN_DATO (correcto por R2).
- **Filtros aplican end-to-end**: `nivel=Primaria` cambia KPI-01 de 5,837 → 1,657 y KPI-02 de
  -117.8% → -14.8% (captura `/tmp/opencode/evidencia/db01-filtrado.png`).
- Suite completa: **256 passed, 4 skipped**; `ruff check` limpio en archivos del cambio
  (los 44 restantes son preexistentes de otras células: `_Meta/scripts`, `dags/`, `src/`).


## Bloqueos / pendientes
- US-212 (Marina) puede arrancar ya contra estos SQL: son el contrato de US-113.
- Al llegar C3 (US-311/313): descartar mock, re-ejecutar sync; nada más cambia.
- KPI-02 muestra -117.8% global: es la variación ponderada REAL del mock (caída fuerte 2024→2025 en
  municipios grandes); al llegar datos reales se re-evalúa. No es bug de formato (verificado).
- Pendiente visual fino (colores del coroplético, tooltips) — ajustes van en `params_extra` del YAML.
- Documentar las `--vars` de dbt en Environment_Setup (fuera de alcance de esta historia).

## 🤖 Sesión de IA
- **Agente / modelo:** OpenCode / opencode/big-pickle
- **Archivos creados/modificados:** `superset/semantic/{db01_*,db02_*}.sql` (6),
  `superset/semantic/metrics_db01_db02.yaml`, `superset/dashboards/*.yaml` (2),
  `superset/mock/gold_ml_outputs_mock.sql`, `superset/assets/geojson/municipios_scope.geojson`,
  `superset/{generar_geojson,cargar_geojson}_municipios.py`, `superset/sync_semantic_layer.py`,
  `docker/superset.Dockerfile`, `superset/README.md`, `tests/test_semantic_db01_db02.py` (nuevo).
- **Fuera de alcance, no editado:** `docker-compose.yml`, `.gitattributes`, código de otras células.
- **Manejo de secretos:** `.env` nunca impreso; credenciales interpoladas solo por shell al crear
  `~/.dbt/profiles.yml` (fuera del repo, permisos 600).
