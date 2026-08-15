---
id: DOC-ML02-CLASIFICACION-DRIVER
title: "ML-02 — Clasificación de driver dominante"
owner: "Andrés González Habib"
status: draft
version: "0.1"
traces_up: ["US-302", "REQ-003", "15_ML_Models/ML_Strategy"]
traces_down: ["src/modelos/entrenar_ml02.py", "tests/test_entrenar_ml02.py"]
tags: [ml, ml-02, clasificacion, shap, celula-3]
---

# ML-02 — Clasificación de driver dominante

> → [[15_ML_Models/_index]] · [[15_ML_Models/ML_Strategy]]

## Objetivo

ML-02 identifica cuál de los seis drivers (`D1`…`D6`) explica mejor el riesgo de una escuela y devuelve
una recomendación prescriptiva alineada con el contrato de la API.

## Estado actual

El scaffold ejecutable vive en `src/modelos/entrenar_ml02.py` y ya permite avanzar sin esperar a Gold:

- carga `tests/fixtures/features_escuela_mock.csv` o una tabla compatible con `gold.features_escuela`;
- reutiliza backtesting temporal (`generar_backtesting` + `verificar_sin_fuga`);
- entrena `HistGradientBoostingClassifier`, que tolera `NaN` para preservar `SIN_DATO`;
- reporta `F1 macro`, `accuracy`, `precision macro` y baseline `most_frequent`;
- produce `driver_dominante` (`D1`…`D6`) y `recomendacion` para integración posterior con API.
- puede registrar el modelo de producción en MLflow con el nombre canónico `ML02_DriverClasificador`
	cuando el ambiente tenga `mlflow` configurado.

## Target provisional

El contrato vigente de `gold.features_escuela` todavía no incluye `driver_dominante`. Para evitar un
bloqueo, el script deriva `driver_dominante_proxy` con el driver observado de mayor puntaje. Los
drivers con `SIN_DATO` quedan como `NaN` y no pueden dominar la fila; no se imputan con cero.

Este proxy sirve para validar pipeline, partición temporal, métricas y forma de salida. No sustituye la
etiqueta supervisada final: cuando Célula 1 publique `driver_dominante` en Gold, el script la usará de
forma preferente y el proxy quedará solo como fallback de desarrollo.

## Explicabilidad

`calcular_shap_kernel()` calcula contribuciones SHAP si el ambiente de Célula 3 tiene instalado `shap`
desde `requirements/celula-3.txt`. La función queda fuera del camino crítico del CI base porque SHAP no
forma parte de `requirements.txt`.

## Validación

Pruebas agregadas en `tests/test_entrenar_ml02.py`:

- derivación de `driver_dominante_proxy` sin convertir `SIN_DATO` en cero;
- rechazo de filas sin ningún driver observado;
- backtesting temporal sin fuga;
- métricas acotadas en `[0,1]`;
- salida con `cct`, `id_ciclo`, `driver_dominante` y `recomendacion`.
- nombre MLflow canónico de ML-02.

## Pendientes para cerrar US-302

- Confirmar con Célula 1 dónde se publica la etiqueta real `driver_dominante`.
- Correr métricas sobre `gold.features_escuela` real, no solo fixture sintético.
- Registrar resultados finales en MLflow como parte de US-303.
- Confirmar el `MLFLOW_TRACKING_URI` local/CI con Célula 5.
- Conectar la explicación SHAP completa al endpoint `/predicciones/{cct}/explicacion` de Célula 4.
