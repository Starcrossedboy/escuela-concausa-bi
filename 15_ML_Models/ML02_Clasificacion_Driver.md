---
id: DOC-ML02-CLASIFICACION-DRIVER
title: "ML-02 — Clasificación de driver dominante"
owner: "Andrés González Habib"
status: in_review
version: "0.3"
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
- produce `driver_dominante` (`D1`…`D6`) y `recomendacion` para integración posterior con API;
- publica las recomendaciones en Gold, alineadas por `cct` e `id_ciclo` con las predicciones de ML-01;
- devuelve explicaciones SHAP por escuela con el contrato `cct`, `driver_dominante` y
	`contribuciones` (`D1`…`D6`);
- puede registrar el modelo de producción en MLflow con el nombre canónico `ML02_DriverClasificador`
	y exige confirmación de la versión creada en el Registry.
- valida antes de entrenar que el target real o proxy no tenga nulos, use solo `D1`…`D6` y contenga
	al menos dos clases.

## Target provisional

El contrato vigente de `gold.features_escuela` todavía no incluye `driver_dominante`. Para evitar un
bloqueo, el script deriva `driver_dominante_proxy` con el driver observado de mayor puntaje. Los
drivers con `SIN_DATO` quedan como `NaN` y no pueden dominar la fila; no se imputan con cero.

Este proxy sirve para validar pipeline, partición temporal, métricas y forma de salida. No sustituye la
etiqueta supervisada final: cuando Célula 1 publique `driver_dominante` en Gold, el script la usará de
forma preferente y el proxy quedará solo como fallback de desarrollo.

## Explicabilidad

`calcular_shap_kernel()` calcula contribuciones SHAP mediante `KernelExplainer` y
`explicar_driver()` las transforma al contrato acordado para Célula 4. SHAP vive en
`requirements/celula-3.txt`, fuera del camino crítico del CI base. El flujo se verificó localmente
con una explicación real de seis contribuciones para una escuela.

## Validación

El 26 de agosto se validó el flujo completo de registro contra un backend SQLite temporal de MLflow
3.15.1: el entrenamiento creó una corrida y registró `ML02_DriverClasificador` versión `1`. Esto
confirma el código cliente y el Registry local; el identificador de corrida es efímero y cambia en
cada ejecución. Aún falta repetir la prueba contra el servidor Docker compartido para cerrar la
validación end-to-end de infraestructura.

Pruebas agregadas en `tests/test_entrenar_ml02.py`:

- derivación de `driver_dominante_proxy` sin convertir `SIN_DATO` en cero;
- rechazo de filas sin ningún driver observado;
- backtesting temporal sin fuga;
- métricas acotadas en `[0,1]`;
- salida con `cct`, `id_ciclo`, `driver_dominante` y `recomendacion`.
- contrato de explicación SHAP con contribuciones `D1`…`D6`;
- publicación de una recomendación por escuela y ciclo en Gold;
- dos escuelas con igual riesgo y distinto driver reciben recomendaciones distintas;
- nombre MLflow canónico de ML-02.
- preferencia del target real y rechazo temprano de etiquetas nulas, desconocidas o monoclase.

## Pendientes para cerrar US-302

- Confirmar con Célula 1 dónde se publica la etiqueta real `driver_dominante`.
- Correr métricas sobre `gold.features_escuela` real, no solo fixture sintético.
- Validar el Registry contra el servidor Docker compartido cuando el entorno local tenga las
	variables de Compose configuradas; el Registry local con MLflow 3.15.1 ya fue verificado.
- Conectar la explicación SHAP completa al endpoint `/predicciones/{cct}/explicacion` de Célula 4.
