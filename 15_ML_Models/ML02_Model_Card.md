---
id: DOC-ML02-CARD
title: "Ficha de Modelo: ML-02 (Clasificación de Driver Dominante)"
owner: "Carlos Guillermo Mayorga Tapia"
status: in_review
source_of_truth: false
traces_up: ["US-324"]
tags: [ml, ml-02, clasificacion, shap, model-card]
---

# Ficha de Modelo: ML-02 (Clasificación de Driver Dominante)

> → [[15_ML_Models/_index|Volver a _index]]

## 1. Propósito
El objetivo de **ML-02** es realizar una clasificación multiclase supervisada para identificar cuál de los 6 drivers principales (D1 a D6) explica mejor el **riesgo de pérdida o variación de matrícula** en una escuela determinada. Es el **corazón prescriptivo del proyecto**, ya que permite emitir recomendaciones diferenciadas para dos escuelas con el mismo índice de riesgo. (Ver: [[15_ML_Models/ML_Strategy]]).

## 2. Features de Entrada
- Columnas provenientes de `gold.features_escuela`.
- **Utiliza exclusivamente los 6 drivers (D1 a D6)**. NO utiliza indicadores presupuestales o académicos directos.
- Exige un manejo estricto de nulos. Carece de imputación ciega para no sesgar las inferencias causales aproximadas que alimentan a las recomendaciones.

## 3. Métrica Obtenida
- **Resultados actuales**: El modelo cuenta con un `F1 macro >= 0.60` y `Precision >= 0.50` en cada clase.
- **Aviso importante sobre el Target**: Se debe indicar que el objetivo real (target utilizado) **sigue siendo un proxy** (`driver_dominante_proxy` derivado del comportamiento híbrido) y requiere confirmación experta antes del despliegue final.
- **Explicabilidad**: Integra `SHAP (KernelExplainer)` obligatorio en el pipeline de MLflow para justificar por qué se seleccionó el driver dominante. (Ver: [[15_ML_Models/ML02_Clasificacion_Driver]]).

## 4. Limitaciones Conocidas
- El objetivo real (target) requiere confirmación experta; actualmente usa un `driver_dominante_proxy` derivado del comportamiento híbrido.
- La interpretabilidad (SHAP) puede ser costosa computacionalmente en el despliegue al calcularse sobre todas las features para cada escuela en inferencia batch.

## 5. Contextos de NO Uso
- **NO usar sin evaluar cobertura**: Si las features críticas de un centro de trabajo (CCT) no existen en Gold, el modelo no debe inventar el driver.
- **NO usar como motor de predicción de riesgo**: ML-02 no predice el riesgo numérico (esa es tarea exclusiva de ML-01). Solo prescribe *causas* asociadas a dicho riesgo.
- **Artefactos que lo consumen**: La salida de este modelo es consumida en el cubo `DB-09 Recomendaciones`.
