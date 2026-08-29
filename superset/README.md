# `superset/` — capa semántica de Superset (convención US-202)

> Convención canónica de la capa semántica de FARO. La fija **Manuel Alejandro Serranía Reinada**
> (Tech Lead C2, **US-202** — REQ-002) y la deben seguir todas las historias que modelan cubos o
> construyen tableros: US-211a, US-211b, US-212, US-213, US-214a/b, US-215a/b.
> Catálogo canónico de KPIs: [[04_UX_Design/Screen_Specs]] · Contrato de cada cubo: `04_UX_Design/Cube_Specs_*.md`.

## Estructura de carpetas

- **Una subcarpeta por contrato de cubos**, con el nombre del dashboard o familia que alimenta:
  - `semantic/` → SQL de datasets virtuales + YAML de métricas:
    - DB-03 y DB-04 (contrato `DOC-CUBESPEC-DB0304`, US-211a · Marina).
    - DB-01 y DB-02 (contrato `Screen_Specs` §2/§4, US-203 · Manuel).
  - `dashboards/` → definición declarativa de tableros (`*.yaml`): charts, layout y filtros nativos.
  - `mock/` → salidas de ML simuladas para desarrollo local mientras llega C3 (US-311/313).
  - `assets/geojson/` → geometrías municipales del alcance (INEGI, filtradas y simplificadas).

## Naming de archivos y de métricas

- **Archivos por cubo:** `<tablero>_<cubo>.sql` (p.ej. `db03_cubo_escuela_360.sql`) — dataset virtual
  de Superset y, a la vez, SQL de referencia para la materialización de la Célula 1 (US-113).
- **Métricas por contrato:** `metrics_<cubos>.yaml` (p.ej. `metrics_db03_db04.yaml`).
- **Nombres de métricas: `snake_case`** y **idénticos a la fórmula del KPI canónico** de
  [[04_UX_Design/Screen_Specs]] (p.ej. `variacion_ponderada_pct` es el nombre del KPI-02). Cada métrica
  declara `kpi: KPI-xx`; si no hay KPI canónico aún, se marca `kpis_propuestos` y se alinea cuando el
  catálogo lo publique. **El catálogo de KPIs es la única fuente de nombres de métricas.**

## Estructura del YAML

| Sección | Contenido |
|---|---|
| `version` / `owner` / `story` / `traces_up` | Metadatos del artefacto (Definition of Filed) |
| `filtros_globales` | Ciclo, entidad y nivel (AC-002.2); acotado a `SCOPE_ENTIDADES` |
| `datasets[].grano` / `llave_primaria` | Grano y llave del cubo |
| `datasets[].banderas_cobertura` | Todas las banderas de cobertura del cubo |
| `datasets[].jerarquias` | Rutas de drill-down (territorio, tiempo, oferta) |
| `datasets[].metricas` | Nombre, etiqueta, expresión, formato y `kpi` al que sustenta |
| `drill_down` | Navegación cruzada entre tableros (US-214a) |

## Reglas no negociables (heredadas de Screen_Specs y Data_Model)

1. **Salidas de ML siempre por `JOIN`** (`gold.predicciones` / `gold.recomendaciones`), nunca como
   columna del hecho. En el **grano de escuela el `JOIN` es `LEFT`** para que la ficha exista aunque el
   modelo aún no haya puntuado (ratificado 2026-08-15 en Screen_Specs §4).
2. **`SIN_DATO` explícito: nunca cero, nunca nulo silencioso.** Prohibido `COALESCE(<driver>, 0)`.
   Cada métrica viaja con su bandera de cobertura y muestra "sin dato disponible".
3. **Umbral de riesgo `>= 0.6`** (≈ perder ~5% de matrícula), ratificado el 2026-08-13.
4. **Razones como componentes aditivos:** numerador y denominador por separado
   (`suma_*` / `escuelas_con_*`), para que se reagreguen bien con cualquier combinación de filtros.
5. Toda división se protege con `NULLIF(denominador, 0)`.

## Validación

- Validación **estática** por contrato: `pytest tests/test_semantic_db03_db04.py -q`
  y `pytest tests/test_semantic_db01_db02.py -q`.
- Validación **contra datos** (local): `python superset/sync_semantic_layer.py --validar-datos`
  consulta cada chart contra Postgres y reporta filas o error SQL.

## Cadena local completa (US-203)

Con Docker arriba (`docker compose up -d db superset`) y `.env` cargado:

```bash
source .venv/bin/activate
# 1) Bronze: fixtures sintéticos a bronze.* (idempotente)
#    ver src/ingesta/cargar_bronze_fixture.py
# 2) Silver + Gold con dbt (los datasets virtuales son también el SQL de
#    referencia para la materialización de US-113):
#    dbt run --select ... --vars '{...}'   (vars de identificadores de fuentes)
# 3) Mock de ML-01/ML-02 (MIENTRAS C3 no entrega; marcado MOCK-US203):
docker exec -i faro-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    < superset/mock/gold_ml_outputs_mock.sql
# 4) Geometrías municipales (una sola vez; asset versionado en el repo):
set -a; source .env; set +a
python superset/cargar_geojson_municipios.py
# 5) Sincronizar datasets + métricas + charts + tableros:
python superset/sync_semantic_layer.py --validar-datos
```

Tableros resultantes: `http://127.0.0.1:8088/superset/dashboard/db01-ejecutivo/` y
`http://127.0.0.1:8088/superset/dashboard/db02-mapa-riesgo/`.

### Workaround: charts colgados en "Waiting on faro_escuela_concausa_db"

Síntoma observado (US-203, 2026-08-22): un tablero carga y el otro se queda con todos los charts
en "Waiting on ..." indefinidamente, sin errores en consola ni peticiones `POST /api/v1/chart/data`
en la red del navegador; las SQL corren en milisegundos directo contra Postgres.

- **Causa probable:** caché de metadatos/resultados en memoria de Superset (esta imagen no tiene
  Redis ni backend de resultados externo) que quedó en mal estado tras una corrida del sync.
- **Workaround:** reiniciar solo el contenedor de BI — `docker restart faro-superset` — esperar el
  healthcheck (`docker ps` → *healthy*, ~30 s) y recargar con hard-refresh (Ctrl/Cmd+Shift+R).
  Verificado: tras el restart ambos tableros cargan completos en ~2 s.
- Si reaparece, reportarlo en `06_Quality_Testing/Bug_Register.md` citando este README.
- Fix definitivo (C5, backlog): backend de caché/resultados externo (Redis) o al menos
  `DATA_CACHE_CONFIG` persistente en `superset_config.py`.

### Notas del mock (`mock/gold_ml_outputs_mock.sql`)

- Solo desarrollo local: valores determinísticos por hash del CCT, `mlflow_run_id = 'MOCK-US203'`.
- Idempotente (`ON CONFLICT DO NOTHING`) y sin DDL destructivo; único cambio de esquema permitido:
  `ADD COLUMN IF NOT EXISTS` para completar DEC-005 si la tabla local quedó mínima.
- Deja un municipio completo sin predicciones a propósito: ejercita `cobertura_riesgo = 'SIN_DATO'`.
- Se descarta cuando C3 publique las salidas reales en `gold.predicciones` / `gold.recomendaciones`.

### Notas del GeoJSON (`assets/geojson/municipios_scope.geojson`)

- Fuente: espejo comunitario del Marco Geoestadístico INEGI (CONABIO 2023, MIT) — datos públicos.
- Filtrado a `SCOPE_ENTIDADES` (09, 14, 15, 19), simplificado (Douglas-Peucker ~200 m) hasta ~600 KB.
- Regenerable: `python superset/generar_geojson_municipios.py --descargar <dir>` + `--generar <dir>`.
- La llave de cada feature es `cve_mun` (CVEGEO de 5 dígitos) = `gold.dim_municipio.cve_mun`.

## Responsables

- **Convención (US-202):** Manuel Alejandro Serranía Reinada (Tech Lead C2).
- **Contenido por historia:** el owner de cada US-211a/b…215a/b declara sus datasets/métricas
  siguiendo esta convención y alineando nombres con el catálogo de KPIs.
