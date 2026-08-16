# `superset/` — capa semántica de Superset (convención US-202)

> Convención canónica de la capa semántica de FARO. La fija **Manuel Alejandro Serranía Reinada**
> (Tech Lead C2, **US-202** — REQ-002) y la deben seguir todas las historias que modelan cubos o
> construyen tableros: US-211a, US-211b, US-212, US-213, US-214a/b, US-215a/b.
> Catálogo canónico de KPIs: [[04_UX_Design/Screen_Specs]] · Contrato de cada cubo: `04_UX_Design/Cube_Specs_*.md`.

## Estructura de carpetas

- **Una subcarpeta por contrato de cubos**, con el nombre del dashboard o familia que alimenta:
  - `semantic/` → cubos de DB-03 y DB-04 (contrato `DOC-CUBESPEC-DB0304`, US-211a · Marina).
  - Las próximas familias (p.ej. DB-05/DB-08, US-211b) crean su propia subcarpeta o extienden
    `semantic/` si comparten contrato — decidir al modelar, sin duplicar métricas.

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

- Validación **estática** por contrato: `pytest tests/test_semantic_db03_db04.py -q`.
- La validación **contra datos reales** queda pendiente hasta que la Célula 1 entregue `gold.*` (US-112/113).

## Responsables

- **Convención (US-202):** Manuel Alejandro Serranía Reinada (Tech Lead C2).
- **Contenido por historia:** el owner de cada US-211a/b…215a/b declara sus datasets/métricas
  siguiendo esta convención y alineando nombres con el catálogo de KPIs.
