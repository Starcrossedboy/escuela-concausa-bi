---
id: DOC-ML-STRATEGY
title: "Estrategia de Modelado ML — FARO"
owner: "Andrés González Habib"
status: approved
version: "1.0"
traces_up: ["REQ-003", "03_Architecture/ADRs/ADR-003-ml-estrategia-modelado"]
traces_down: ["US-301", "US-302", "US-303"]
last_reviewed: "2026-08-09"
tags: [ml, strategy, celula-3, modelado]
---

# Estrategia de Modelado ML — FARO

> Documento canónico de diseño para los 3 modelos de ML de FARO.
> La decisión de arquitectura está en [[03_Architecture/ADRs/ADR-003-ml-estrategia-modelado]].
> → [[15_ML_Models/_index]]

---

## 1. Los 3 modelos

| ID | Nombre | Tipo | Variable objetivo | Métrica | Sprint |
|---|---|---|---|---|---|
| ML-01 | Regresión de matrícula | Supervisado · regresión | `delta_matricula` (variación absoluta de alumnos al siguiente ciclo) | MAE / RMSE | S4 |
| ML-02 | Clasificación de driver dominante | Supervisado · multiclase | `driver_dominante` (1 de 6 drivers) | F1 macro + SHAP | S4 |
| ML-03 | Clustering de escuelas | No supervisado | — (agrupación por perfil) | Silhouette | S4 |

**ML-02 es el corazón prescriptivo**: dos escuelas con el mismo riesgo reciben recomendaciones
distintas según el driver dominante identificado.

---

## 2. Fuente de datos

Todos los modelos consumen **`gold.features_escuela`** (US-104, Diana Alvarez, C1).

Mientras `gold.features_escuela` no esté disponible, se trabaja con el fixture mock:
`tests/fixtures/features_escuela_mock.parquet` (≤500 filas, datos sintéticos).

### Schema esperado de `gold.features_escuela`

| Columna | Tipo | Descripción |
|---|---|---|
| `cct` | `str` | Clave de Centro de Trabajo (llave primaria) |
| `ciclo` | `str` | Ciclo escolar, e.g. `"2022-23"` |
| `entidad_id` | `str` | Clave INEGI de entidad (`"09"`, `"15"`, `"19"`, `"14"`) |
| `nivel` | `str` | Nivel educativo (PREESCOLAR, PRIMARIA, SECUNDARIA, etc.) |
| `matricula` | `int` | Matrícula total del ciclo |
| `delta_matricula` | `float` | Variación respecto al ciclo anterior (target ML-01) |
| `d1_rezago_social` | `float` | Índice CONEVAL de rezago social del municipio |
| `d2_incidencia_delictiva` | `float` | Tasa de delitos por 100k hab. (SESNSP) |
| `d3_infraestructura_score` | `float` | Score compuesto de infraestructura (CEMABE) |
| `d4_conectividad_score` | `float` | Score de conectividad digital (CEMABE) |
| `d5_estres_hidrico` | `float` | Índice de estrés hídrico (CONAGUA SINA) |
| `d5_dato_disponible` | `int` | 1 si hay dato real, 0 si es imputación |
| `d6_calidad_aire` | `float` | Índice de calidad del aire (SINAICA) |
| `d6_dato_disponible` | `int` | 1 si hay dato real, 0 si es imputación |
| `indice_completitud_drivers` | `float` | Fracción de drivers con dato real [0.0–1.0] |
| `driver_dominante` | `str` | Target ML-02: driver que más explica el riesgo |

---

## 3. Partición temporal

**Regla no negociable:** nunca split aleatorio (produce fuga de información en series de tiempo).

### Walk-forward de 1 ciclo

```
Ciclos disponibles: 2013-14, 2014-15, …, 2023-24  (10 ciclos)

Fold 1: train = [2013-14 … 2019-20]  |  test = [2020-21]
Fold 2: train = [2013-14 … 2020-21]  |  test = [2021-22]
Fold 3: train = [2013-14 … 2021-22]  |  test = [2022-23]
Fold 4: train = [2013-14 … 2022-23]  |  test = [2023-24]  ← fold de producción
```

La métrica reportada es **promedio ± desviación estándar** de los 4 folds.

### Implementación

```python
from src.modelos.utils.temporal_split import walk_forward_splits

for train_idx, test_idx in walk_forward_splits(df, ciclo_col="ciclo", n_folds=4):
    X_train, X_test = df.iloc[train_idx], df.iloc[test_idx]
    # ...
```

---

## 4. Manejo de cobertura parcial (D5 y D6)

D5 (agua) cubre zonas regionales; D6 (aire) cubre ~80 zonas urbanas.
En escuelas fuera de cobertura, se aplica:

1. Imputación con **mediana histórica del municipio** (si existe al menos 1 ciclo con dato real).
2. Imputación con **mediana estatal** si el municipio tampoco tiene datos.
3. El indicador `d5_dato_disponible` / `d6_dato_disponible` se pone en `0` siempre que se imputa.

**Nunca se introduce `0` como valor del índice** (cero es dato físicamente válido para algunos
indicadores).

---

## 5. Umbrales de aceptación (provisionales)

Los umbrales se definen ahora sobre datos mock y se confirmarán con datos reales (US-104).

| Modelo | Métrica | Umbral mínimo |
|---|---|---|
| ML-01 | MAE | < 15 alumnos |
| ML-01 | RMSE | < 25 alumnos |
| ML-02 | F1 macro | ≥ 0.60 |
| ML-02 | Precision por clase | ≥ 0.50 en cada clase |
| ML-03 | Silhouette | ≥ 0.30 |

Si el modelo no alcanza el umbral en el fold de producción (Fold 4), se bloquea el merge del PR.

---

## 6. Explicabilidad — ML-02

ML-02 usa **SHAP (TreeExplainer)** para:

- Calcular la contribución de cada driver a la predicción de cada escuela.
- Identificar el `driver_dominante` como el feature con mayor `|SHAP value|`.
- Permitir que dos escuelas con igual riesgo reciban recomendaciones distintas (AC-003.6).

Salida esperada del endpoint de ML-02:

```json
{
  "cct": "09DPR1234X",
  "driver_dominante": "d2_incidencia_delictiva",
  "shap_values": {
    "d1_rezago_social": -0.12,
    "d2_incidencia_delictiva": 0.54,
    "d3_infraestructura_score": 0.08,
    "d4_conectividad_score": -0.03,
    "d5_estres_hidrico": 0.11,
    "d6_calidad_aire": 0.02
  },
  "recomendacion": "Intervención prioritaria en seguridad del entorno escolar."
}
```

---

## 7. Registro en MLflow

Cada modelo se registra con:

```python
mlflow.log_params({"modelo": "ML-02", "fold": fold_n, "features": len(X_train.columns)})
mlflow.log_metrics({"f1_macro": f1, "precision_macro": prec})
mlflow.sklearn.log_model(model, artifact_path="ml02_driver_classifier")
mlflow.register_model(f"runs:/{run.info.run_id}/ml02_driver_classifier", "ML02_DriverClasificador")
```

El nombre canónico de los modelos en el registry es:
- `ML01_RegresionMatricula`
- `ML02_DriverClasificador`
- `ML03_ClusteringEscuelas`

---

## 8. Tests requeridos (US-301)

| ID | Qué verifica | Archivo |
|---|---|---|
| TEST-ML-001 | No hay fuga temporal: ningún `ciclo` del test aparece en train | `tests/test_temporal_split.py` |
| TEST-ML-002 | No hay nulos ni ceros en features de drivers con `dato_disponible=0` | `tests/test_fixtures.py` |
| TEST-ML-003 | El schema del fixture mock coincide con el schema esperado de `gold.features_escuela` | `tests/test_fixtures.py` |
