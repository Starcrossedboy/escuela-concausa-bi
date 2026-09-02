---
project: "FARO"
date: "2026-08-22"
author_human: "Manuel Alejandro Serrania Reinada"
agent: "OpenCode"
model: "ox-alpha"
type: devlog
session_duration: "~2h"
touches: ["US-203", "REQ-002", "AC-002.2", "AC-002.3", "KPI-01", "KPI-02", "KPI-03", "KPI-04", "KPI-07", "KPI-08", "KPI-09"]
tags: [devlog, bi, superset, filtros-globales, geojson, celula-2]
---

# 2026-08-22 — Manuel Serranía · US-203 sesión 3: filtros AC-002.2 completos + nombres reales

## Qué se hizo

### 1. Los 3 gaps de filtros (AC-002.2) corregidos

| Gap | Fix |
|---|---|
| DB-02 sin filtro "Entidad" | Nuevo filtro `nombre_entidad` en `db02_mapa_riesgo.yaml` targeting cubo + coroplético + puntos |
| Coroplético ignoraba el filtro Ciclo | `db02_coropletico` agregado a los targets de Ciclo escolar |
| En DB-01, Entidad no alcanzaba pies ni drivers | `cve_ent` (+`nombre_entidad`) entra al grano de `db01_distribucion_escuelas` y `db01_driver_dominante`; Entidad ahora targetea los 3 datasets |

El filtro de Entidad usa **`nombre_entidad`** (opciones legibles: 'Jalisco', 'Nuevo Leon', ...);
`cve_ent` queda expuesta como llave canónica en todos los datasets.

### 2. Bug nuevo del sync descubierto y arreglado

`ensure_datasets` nunca actualizaba el SQL de un dataset existente (solo lo saltaba con "existe").
Los cambios de SQL jamás llegaban a Superset — misma familia del bug de métricas de la sesión 2.
Fix: comparar contra el SQL guardado (`GET /dataset/<id>`) y hacer `PUT {"sql": ...}` si difiere.
Verificado idempotente: segunda corrida reporta "existe y está al día".

### 3. Nombres reales de municipio ("Municipio 09002" → "Azcapotzalco")

- **Causa raíz:** `gold.dim_municipio` es fixture de C1 (10 municipios placeholder). NO es bug de US-203.
- **Mitigación en la capa semántica (alcance US-203):** los 6 SQL hacen
  `COALESCE(g.nombre_municipio, dm.nombre_municipio)` vía LEFT JOIN a `gold.geo_municipio`
  (nombres oficiales INEGI ya cargados por el cargador del GeoJSON). Cuando C1 cargue el catálogo
  real de DS-02, el COALESCE puede invertirse o desaparecer.
- Verificado E2E: rankings muestran Azcapotzalco, Toluca, Coacalco, Apodaca, Monterrey...

### 4. Puntos en líneas paralelas — diagnóstico (no requiere fix en US-203)

Son **datos sintéticos**: el generador de fixtures Bronze de C1
(`tests/fixtures/generate_bronze_cct_conapo_fixtures.py:39-40`) crea coordenadas en rejilla:

```python
lat = round(19.0 + (i % 20) * 0.15, 5)
lon = round(-99.0 - (i % 15) * 0.20, 5)
```

Gold hoy tiene solo 25 escuelas/25 hechos de prueba; las líneas paralelas son esa rejilla.
Se resolverá solo cuando DS-02 (catálogo CCT real) fluya por Airflow/dbt. El scatter está correcto.

### 5. Limpieza pre-PR

- ✅ Eliminado `SESION-RESUMEN-US203.md` de la raíz (autorizado por Manuel).
- ✅ Eliminado dashboard residual "TEST filtros" (id=3) vía API (autorizado).
- ✅ Workaround documentado en `superset/README.md` § "Charts colgados en Waiting on...":
  causa (caché en memoria sin Redis), `docker restart faro-superset`, y fix definitivo para C5.

## Verificación

- `pytest tests/test_semantic_db01_db02.py -q` → **47 passed** (granos actualizados en aserciones)
- Suite completa → **256 passed, 4 skipped**
- `ruff check` → limpio en archivos del cambio
- `vault_lint.py` → ✅ Vault limpio
- Sync re-ejecutado con validación de datos: 16/16 charts OK
- Playwright E2E:
  - DB-02: 3 filtros (Ciclo/Entidad/Nivel); Entidad=Jalisco cambia todos los charts,
    ranking filtrado muestra Guadalajara; captura `evidencia/db02-filtro-jalisco.png`
  - DB-01: Entidad=Nuevo León cambia tiles+serie+ranking+pies+drivers
    (KPI-01 5,837→1,457 · alcance 25→6 · ranking Apodaca/Monterrey);
    captura `evidencia/db01-filtro-nuevoleon.png`

## Notas / riesgos

- Tras cambiar SQL de datasets conviene reiniciar `faro-superset` o esperar expiración de caché;
  el workaround ya está documentado en el README.
- El grano de `db01_driver_dominante` ahora incluye `cve_ent`: COUNT DISTINCT al grano sigue siendo
  correcto (1 escuela = 1 entidad), pero US-113 debe respetar este grano al materializar.
- Pendiente del handoff anterior: rama sin push, PR con aprobación del PM, `graphify update`.
