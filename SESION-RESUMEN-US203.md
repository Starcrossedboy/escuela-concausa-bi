---
id: TEMP-SESION-US203
title: "RESUMEN DE SESIONES US-203 (TEMPORAL)"
owner: "Manuel Alejandro Serrania Reinada"
status: temporal
version: "1.0"
traces_up: ["US-203"]
tags: [temporal, devlog-resumen, celula-2]
---

# RESUMEN DE SESIONES — US-203 (TEMPORAL — eliminar antes del merge a main)

> **Propósito:** plasmación puntual de TODO lo trabajado en las sesiones de IA para US-203.
> **Estado:** TEMPORAL en raíz a petición de Manuel Serrania. No forma parte del vault
> (no tiene ID ni frontmatter); el registro canónico vive en `_DevLog/2026-08-21-manuel-serrania-us203-tableros-db01-db02.md`
> y `_DevLog/2026-08-22-handoff-us203-tableros-superset.md`.
> **Historia:** US-203 — Manuel Alejandro Serrania Reinada (Célula 2, Analytics & BI)
> **Rama:** `feat/manuel-serrania-us203-dashboards-insignia`

---

## Sesión 1 (2026-08-21) — Construcción

### 1. Capa semántica declarativa (`superset/semantic/`)
| Archivo | Qué es |
|---|---|
| `db01_cubo_matricula.sql` | Grano `cve_mun × nivel × ciclo`; componentes aditivos (`variacion_x_matricula`, `suma_completitud`), sin promedios precalculados (patrón DEC-008) |
| `db02_cubo_riesgo_territorial.sql` | Riesgo por LEFT JOIN a `gold.predicciones` (`cct+id_ciclo+modelo='ML-01'`), denominador real `escuelas_con_prediccion`, bandera `cobertura_riesgo='SIN_DATO'` (R1/R2/R3) |
| `db01_distribucion_escuelas.sql` | KPI-08 (nivel) / KPI-09 (sostenimiento) |
| `db01_driver_dominante.sql` | KPI-07, LEFT JOIN a `gold.recomendaciones`, etiqueta SIN_DATO |
| `db02_puntos_escuela.sql` | Scatter al grano cct × ciclo con lat/long y riesgo |
| `db02_coropletico.sql` | Cubo + geometrías; SIN `nivel` en el grano a propósito (evita polígonos duplicados) |
| `metrics_db01_db02.yaml` | 6 datasets, métricas SUM/SUM con NULLIF, `% en riesgo` divide entre escuelas puntuadas |

### 2. Tableros declarativos (`superset/dashboards/`)
- `db01_ejecutivo.yaml`: 9 charts (4 tiles KPI, serie temporal, ranking municipal, 2 pies, drivers).
- `db02_mapa_riesgo.yaml`: 7 charts (tiles KPI-03/04, coroplético deck_polygon, scatter deck_scatter, ranking).
- Filtros globales declarados por tablero: ciclo escolar / entidad federativa / nivel educativo (AC-002.2).

### 3. Sync idempotente (`superset/sync_semantic_layer.py`)
- Crea/actualiza database → datasets → métricas/dimensiones → charts → dashboards vía API REST.
- Valida cada chart contra datos reales con el endpoint bulk `POST /api/v1/chart/data`.
- Arma bundle de importación v1 en memoria (ZIP multipart) porque el PUT REST de dashboards NO llena `dashboard_slices`.

### 4. Mock local ML (`superset/mock/gold_ml_outputs_mock.sql`)
- Determinístico por hash del CCT, marcado `mlflow_run_id='MOCK-US203'`, idempotente, no destructivo.
- Siembra catálogo `dim_driver` D1–D6 completo; deja un municipio sin predicciones para ejercitar SIN_DATO.

### 5. GeoJSON municipal (`superset/assets/geojson/municipios_scope.geojson`, 608 KB)
- Espejo comunitario INEGI/CONABIO 2023 (MIT), filtrado al scope (317 municipios), simplificado ~200 m.
- `generar_geojson_municipios.py` + `cargar_geojson_municipios.py` → `gold.geo_municipio`.

### 6. Fix de ambiente (señalado a C5)
- `docker/superset.Dockerfile`: `pip install psycopg2-binary` instalaba fuera del venv `/app/.venv`
  gestionado por uv → "No module named psycopg2". Corregido a `uv pip install --python /app/.venv/bin/python`.

---

## Sesión 2 (2026-08-22) — Depuración con Playwright tras revisión de Manuel

Manuel reportó tiles vacíos/texto cortado. Se instrumentó Chromium headless (login por UI,
DOM + consola + red + Redux). **Cuatro bugs reales, todos del script de sync:**

1. **`% escuelas en riesgo = 3,181.8%`** — doble escalado: expresión SQL con `*100` Y formato d3
   `,.1%` que multiplica otra vez. Fix: razón pura en YAML (0.318 → "31.8%") y UN solo mapa de
   formatos (`FORMATO_D3`); se eliminó `_FORMAT_MAP` divergente.
2. **Métricas de dataset nunca se actualizaban** — el sync se saltaba las existentes y mandaba el
   formato como `extra.d3Format` (campo inexistente; el schema es `d3format`). Además el PUT exige
   `id` numérico para distinguir update de alta (`_validate_metrics`), si no rechaza 422 "already exist".
3. **Scatter sin puntos** — claves correctas del bloque `spatial` son `lonCol`/`latCol`
   (no `longitudeCol`/`latitudeCol`); verificado contra el bundle JS compilado.
4. **Barra de filtros nativos no montaba** — el enum del frontend es `'VERTICAL'/'HORIZONTAL'`
   en MAYÚSCULAS (`FilterBarOrientation`) y escribíamos `"vertical"` minúsculas; ninguna comparación
   del DashboardBuilder hacía match → falla silenciosa sin errores de consola. Diagnosticado leyendo
   Redux desde el fiber de React vía Playwright. Fix: `"VERTICAL"`.

### Evidencia final verificada
| Verificación | Resultado |
|---|---|
| DB-01 | 9/9 charts con datos (tiles, serie canvas, tabla 9 filas, 3 pies) |
| DB-02 | 7/7 charts (coroplético con leyenda, scatter con canvas, N/A correcto por R2) |
| Filtro `nivel=Primaria` | KPI-01: 5,837 → 1,657 · KPI-02: -117.8% → -14.8% |
| Barra filtros | Montada (ciclo/nivel/entidad) con Apply/Clear funcionales |

---

## Hallazgos de compatibilidad Superset 6.1 (para futuras células)

1. Tipos de filtro: `filter_select`/`filter_range`/`filter_time`/... (el viejo `native_filters.SelectFilter` no existe).
2. `dashboard_slices` SOLO lo llena la importación v1; el PUT REST no asocia charts.
3. Importador v1: ZIP con carpeta raíz + `metadata.yaml`; cada YAML un único mapeo; targets planos con `datasetUuid`.
4. `overwrite=true` va en el FORM del multipart, no en query string.
5. Rate limit 50 req/s → reintentos ante 429.
6. Validación de datos: endpoint bulk `POST /api/v1/chart/data` (el `GET /chart/<id>/data` no existe).
7. PUT de dataset: update vs alta se distingue por `id` numérico de la métrica; campo de formato es `d3format`.
8. `FilterBarOrientation` = 'VERTICAL'/'HORIZONTAL' (mayúsculas) en `json_metadata`.

---

## Estado de verificación

- `pytest tests/test_semantic_db01_db02.py -q` → **47 passed**
- Suite completa → **256 passed, 4 skipped**
- `ruff check` limpio en archivos del cambio (los 44 restantes son preexistentes de otras células:
  `_Meta/scripts/`, `dags/`, `src/`)
- `vault_lint.py` → ✅ Vault limpio
- Sync idempotente: segunda corrida crea 0 objetos, sin duplicados
- Capturas Playwright: `/tmp/opencode/evidencia/db01-filtrado.png` y `db0*-final.png`

## Notas honestas

- **KPI-02 global (-117.8%)**: variación ponderada REAL del mock (caída fuerte 2024→2025 en municipios
  grandes). No es bug de formato; se re-evalúa al llegar datos de C3.
- US-212 (Marina) puede arrancar ya: estos SQL son el contrato de US-113.
- Al llegar C3 (US-311/313): descartar mock y re-ejecutar sync; nada más cambia.
