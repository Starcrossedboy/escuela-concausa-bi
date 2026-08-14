---
project: "FARO"
date: "2026-08-13"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "3h"
touches: ["US-311", "REQ-003", "TEST-005", "DOC-ML01-ENTRENAMIENTO", "ML-01", "MOC-MLMODELS"]
tags: [devlog, celula-3, ml, ml-01, mlflow]
---

# DevLog — 2026-08-13 — Entrenamiento y backtesting de ML-01 (US-311)

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

El entregable central de US-311, que el `Execution_Status` tenía anotado como faltante: **modelo
entrenado, MAE/RMSE con backtesting temporal y registro en MLflow** (AC-003.2, AC-003.3, AC-003.4).

- `src/modelos/entrenar_ml01.py` — pipeline completo: carga con validación de contrato, backtesting
  walk-forward, comparación contra baseline, desglose de error por entidad y registro en MLflow.
- `tests/test_entrenar_ml01.py` — 15 casos ([[15_ML_Models/ML01_Entrenamiento|TEST-005]]).
- [[15_ML_Models/ML01_Entrenamiento]] — resultados y protocolo, en `in_review`.

### Resultados (datos sintéticos)

| Ventana | MAE | RMSE | MAE baseline | Mejora |
|---|---|---|---|---|
| entrena 2019-2021 → prueba 2021-2022 | 0.0128 | 0.0168 | 0.0294 | 56.5 % |
| entrena 2019-2022 → prueba 2022-2023 | 0.0138 | 0.0175 | 0.0283 | 51.3 % |
| entrena 2019-2023 → prueba 2023-2024 | 0.0157 | 0.0187 | 0.0295 | 46.8 % |

**MAE 0.0141 ± 0.0012 · RMSE 0.0177 ± 0.0008** (promedio ± desviación, ADR-003).

> Son métricas sobre el fixture **sintético**: validan que el pipeline funciona, no son resultados
> de negocio. Se re-ejecuta cuando llegue `gold.features_escuela` (US-104, vence el 23 de agosto).

### Decisiones de diseño

**`HistGradientBoostingRegressor`** porque maneja `NaN` de forma nativa: un driver `SIN_DATO` llega
al modelo como ausencia real y nunca se imputa a cero (regla 4). Esto **difiere de ADR-003**, que
propone imputación por mediana municipal más indicador binario. Ambas son defendibles; ésta preserva
la señal de ausencia sin inflar la dimensionalidad. Queda anotado como punto a ratificar con Andrés.

**Baseline obligatorio en cada ventana.** Una métrica sin baseline no dice nada: un MAE de 0.015
puede ser excelente o ridículo según la escala del objetivo.

**`entrenar_y_evaluar` es puro respecto a MLflow.** El registro vive en una función aparte, así el
CI no levanta tracking ni escribe artefactos, y US-312 y US-313 pueden reutilizar el entrenamiento.

### Verificación manual de MLflow

Corrido contra `sqlite:///…` fuera del repo: **4 corridas** (1 padre + 3 ventanas), métricas y
parámetros presentes, modelo publicado en el registry como `ML01_RegresionMatricula`.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `src/modelos/entrenar_ml01.py`, `tests/test_entrenar_ml01.py`,
  `15_ML_Models/ML01_Entrenamiento.md`, `15_ML_Models/_index.md`,
  `06_Quality_Testing/Automated/_index.md`
- **Decisiones autónomas del agente:**
  - Elegir `HistGradientBoostingRegressor` por su manejo nativo de nulos, y documentar la
    divergencia con ADR-003 en vez de resolverla por cuenta propia.
  - Separar entrenamiento de registro en MLflow para que el CI no dependa del tracking.
  - Incluir baseline y `mejora_sobre_baseline` en cada ventana.
  - Derivar el error por entidad del CCT, reutilizando `entidad_de_cct()`.
  - Bajar a 3 ventanas por los 5 ciclos del fixture, documentando que ADR-003 pide 4 y que con datos
    reales se sube sin tocar código.
- **Correcciones manuales:** revisión línea por línea. La revisión encontró un defecto en una prueba
  propuesta por la IA: `test_no_imputa_los_sin_dato` afirmaba detectar un `fillna(0)` usando
  `(matriz == 0) & matriz.isna()`, expresión **siempre falsa** porque un `NaN` nunca es igual a 0.
  La prueba pasaba sin verificar nada. Se reescribió para comparar el conteo de nulos que recibe el
  estimador contra el de origen, y se comprobó que con un `fillna(0)` la aserción efectivamente
  falla (405 nulos → 0). También se corrigió un `RUF010` señalado por ruff.
- **Prompt inicial:** avanzar con el entrenamiento de ML-01 tras validar el estado del repositorio.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Tests agregados (TEST-005) — 15 casos; suite completa **65 passed, 4 skipped**
- [x] DevLog enlaza a los IDs afectados
- [x] `ruff check` limpio en los archivos propios
- [x] `vault_lint.py` ✅ · `validate_pm_dashboard.py` ✅
- [x] Sin datos reales: se entrena contra el fixture sintético. La base de MLflow se escribió fuera
      del repositorio para no dejar residuos versionables.

## Bloqueantes

- **`gold.features_escuela`** (US-104, Diana, vence **23 ago**): sin ella las métricas siguen siendo
  sobre datos sintéticos. El pipeline ya está listo; sólo cambia `--features`.
- **MLflow desplegado** (C5): el `docker-compose.yml` del PR #25 trae Postgres y la API, **no
  MLflow**. Se sigue usando SQLite local.
- **`mlflow.db` fuera de `.gitignore`**: el archivo cubre `airflow.db` y `superset.db` pero no
  `mlflow.db`, que es justo el backend que MLflow 3.x exige tras deprecar el file store.

## Riesgos abiertos

- **Divergencia de cobertura parcial** entre esta implementación (`NaN` nativo) y ADR-003
  (imputación por mediana + indicador). Hay que decidir cuál manda antes de cerrar US-311.
- **Umbrales en unidades distintas:** `ML_Strategy` §5 fija `MAE < 15 alumnos`, pero el contrato
  define el objetivo como variación (float). Los umbrales no son comparables tal como están.
- **Duplicación en `main`** (PR #8 vs PR #12): sigue sin resolverse; 4 de las 5 pruebas del #12
  continúan en skip.
- **`gold.predicciones` sin columna `indice_riesgo`:** la SQL del PR #27 de Manuel hace
  `AVG(p.indice_riesgo)`, pero el `Data_Model` §4.5 declara `valor` genérico. Se decide en US-313.

## Próximos pasos

- Re-ejecutar contra features reales en cuanto Diana entregue US-104.
- Ratificar con Andrés el manejo de cobertura parcial.
- US-312: la evaluación ya tiene su insumo (error por entidad y métricas por ventana).
- US-313: el `run_id` del padre de MLflow es el que va a `gold.predicciones.mlflow_run_id`.
