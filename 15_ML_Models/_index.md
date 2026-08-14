---
id: MOC-MLMODELS
title: "ML Models — Índice"
owner: "Andrés González Habib"
status: active
source_of_truth: true
tags: [index, moc, ml]
---

# 15_ML_Models — Modelos de Machine Learning

> El PRD exige **3 modelos de tipos distintos**: regresión/series, clasificación y no supervisado.
> Todos expuestos vía API.

## Los 3 modelos

| ID | Modelo | Tipo | Predice | Métrica | Estado |
|---|---|---|---|---|---|
| ML-01 | Regresión de matrícula | Supervisado · regresión | Variación de matrícula por escuela | MAE / RMSE | pendiente |
| ML-02 | Clasificación de driver | Supervisado · multiclase | Cuál de los 6 drivers explica el riesgo | F1 macro | pendiente |
| ML-03 | Clustering de escuelas | No supervisado | Grupos de perfil similar | Silhouette | pendiente |

**ML-02 es el corazón prescriptivo del proyecto**: permite que dos escuelas con el mismo riesgo
reciban recomendaciones distintas.

## Reglas de modelado no negociables

1. **Partición temporal, nunca aleatoria.** Una partición aleatoria produce fuga de información.
2. **Backtesting obligatorio.** Reportar la métrica real, no la de entrenamiento.
3. **Explicabilidad con SHAP** en ML-02. Sin explicabilidad no hay recomendación defendible.
4. **Cobertura parcial explícita.** Las features con `SIN_DATO` no se imputan con cero.
5. **Todo modelo se registra en MLflow** con parámetros, métricas y artefacto versionado.

## Documentos

| Artefacto | Descripción |
|---|---|
| [[15_ML_Models/ML_Strategy]] | Estrategia de modelado, partición temporal, backtesting, schema de features, umbrales (US-301) |
| [[15_ML_Models/Indice_Riesgo_ML01]] | Conversión de la variación de matrícula predicha por ML-01 al `indice_riesgo` ∈ [0,1] que consumen la API, los cubos y los tableros (US-311) |
| [[15_ML_Models/ML01_Entrenamiento]] | Entrenamiento de ML-01, backtesting walk-forward, resultados y registro en MLflow (US-311) |
