# `superset/semantic/` — capa semántica de DB-03 y DB-04

Artefactos de **US-211a** (Marina García del Buey, Célula 2 · Analytics & BI).
Contrato canónico: [`04_UX_Design/Cube_Specs_DB03_DB04.md`](../../04_UX_Design/Cube_Specs_DB03_DB04.md)
(`DOC-CUBESPEC-DB0304`).

| Archivo | Qué es |
|---|---|
| `db03_cubo_escuela_360.sql` | SQL del cubo de **DB-03 Ficha de escuela**. Grano `cct × id_ciclo`. |
| `db04_cubo_comparador_municipio.sql` | SQL del cubo de **DB-04 Comparador de municipios**. Grano `cve_mun × nivel × id_ciclo`. |
| `metrics_db03_db04.yaml` | Métricas, jerarquías, filtros globales y rutas de drill-down de ambos tableros. |

## Para qué sirve cada cosa

Los dos `.sql` tienen **doble uso**:

1. **Dataset virtual de Superset** — se pegan tal cual al crear el dataset en US-212, para poder
   construir los tableros antes de que existan los cubos físicos.
2. **SQL de referencia para la Célula 1** — son el insumo de **US-113** (construcción de los cubos de
   agregación, Deni Garrido). La materialización en `dbt/`, los índices y la estrategia de refresco
   **son decisión de la Célula 1**, no de este directorio.

## Reglas que estos archivos respetan

- Las salidas de ML (`indice_riesgo`, `driver_dominante`, `recomendacion`) se leen **siempre por
  `JOIN`** a `gold.predicciones` / `gold.recomendaciones`, nunca como columna del hecho
  (`Data_Model` §4.1). En el grano de escuela el `JOIN` es **`LEFT`**, para que la ficha exista aunque
  el modelo aún no haya puntuado a la escuela.
- **`SIN_DATO` explícito: nunca cero, nunca nulo silencioso.** No hay un solo `COALESCE(<driver>, 0)`.
  Cada métrica viaja con su bandera de cobertura y el tablero muestra *"sin dato disponible"*.
- **Umbral de riesgo `>= 0.6`** (≈ perder ~5% de matrícula), ratificado el 2026-08-13.
- Las razones se guardan como **numerador y denominador por separado**, para que se puedan reagregar
  con cualquier combinación de los filtros globales (ciclo, entidad, nivel).

## Cómo se validan

```bash
pytest tests/test_semantic_db03_db04.py -q
```

Es una validación **estática**: no necesita base de datos ni dependencias fuera de
`requirements.txt`. Comprueba el grano, las llaves, la prohibición de `COALESCE(...,0)` sobre drivers
y que las salidas de ML solo aparezcan vía `JOIN`. La validación **contra datos reales queda pendiente**
hasta que la Célula 1 entregue `gold.*` (US-112 / US-113).

## Pendientes de coordinación

- **Diana Alvarez (C1):** cambio de grano de `cubo_comparador_municipio` a `municipio × nivel × ciclo`
  (§8.1 del contrato) y confirmación de cómo se codifica `SIN_DATO` en `d1`…`d6` (§8.2).
- **Manuel Serranía (C2):** alta de KPI-15…KPI-18 en el catálogo, ratificación del `LEFT JOIN` y
  adopción de esta convención de carpeta en **US-202**.
