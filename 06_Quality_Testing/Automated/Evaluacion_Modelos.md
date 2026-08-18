---
id: DOC-EVALUACION-MODELOS
title: "Evaluación comparativa de modelos y análisis de error"
owner: "Héctor Rafael Morales Marbán"
status: in_review
traces_up: ["02_Requirements/Requirements_Detailed", "15_ML_Models/ML_Strategy"]
traces_down: ["US-312"]
tags: [qa, ml, celula-3, metricas]
---

# Evaluación comparativa de modelos y análisis de error

> **Documento generado por `src/modelos/evaluar.py`. No editar a mano.**
> Regenerar con `python -m src.modelos.evaluar`. Así las cifras del vault no se desincronizan de
> las que produce el pipeline, que es lo que exige AC-003.2 al pedir métricas *reproducibles*.
> → [[06_Quality_Testing/Automated/_index]] · [[15_ML_Models/ML01_Entrenamiento]] · [[15_ML_Models/ML_Strategy]]

> [!warning] Métricas sobre datos sintéticos
> Se evalúa contra `tests/fixtures/features_escuela_mock.csv`. Las cifras validan que el pipeline
> de evaluación funciona; **no son resultados de negocio**. Se regeneran cuando la Célula 1
> publique `gold.features_escuela` (US-104).

## 1. Tabla comparativa

| modelo | tipo | metrica | valor | desviacion | baseline | mejora | ventanas |
|---|---|---|---|---|---|---|---|
| ML-01 | regresión | MAE | 0.0141 | 0.0012 | 0.0291 | 0.5155 | 3 |
| ML-02 | clasificación | F1 macro | 0.7945 | 0.0241 | 0.0699 | 10.5571 | 3 |

ML-01 y ML-02 optimizan cosas distintas —error absoluto contra F1—, así que **sus métricas no se
comparan entre sí**. Lo comparable es `mejora`: cuánto aporta cada modelo sobre su propio baseline.
Un modelo que no supera su baseline no aporta nada, sin importar qué tan buena se vea su métrica.

ML-02 se entrena hoy contra `driver_dominante_proxy`. Si es el proxy determinista, su F1 mide la capacidad
de recuperar una etiqueta derivada de los propios drivers, **no de predecir un driver observado**;
la cifra se vuelve significativa cuando Gold publique la etiqueta real.

## 2. Curva de error por ventana

| ventana | modelo | ciclo_prueba | metrica | valor | baseline | mejora | n_entrena |
|---|---|---|---|---|---|---|---|
| 1 | ML-01 | 2021-2022 | MAE | 0.0128 | 0.0294 | 0.5654 | 160 |
| 2 | ML-01 | 2022-2023 | MAE | 0.0138 | 0.0283 | 0.5128 | 240 |
| 3 | ML-01 | 2023-2024 | MAE | 0.0157 | 0.0295 | 0.4682 | 320 |
| 1 | ML-02 | 2021-2022 | F1 macro | 0.7874 | 0.0612 | 11.8601 | 160 |
| 2 | ML-02 | 2022-2023 | F1 macro | 0.7693 | 0.0818 | 8.4085 | 240 |
| 3 | ML-02 | 2023-2024 | F1 macro | 0.8269 | 0.0667 | 11.4028 | 320 |

Es la "curva" de la historia en forma de datos: permite ver si el modelo se degrada conforme
predice ciclos más lejanos del inicio de la serie. Se emite como tabla y no como imagen porque un
diff de PR muestra exactamente qué métrica cambió; un PNG sólo se ve distinto. `--figuras` las
renderiza en local para la demo, sin versionarlas.

## 3. Error por entidad (ML-01, ventana de producción)

| entidad | escuelas | mae | desviacion_vs_global |
|---|---|---|---|
| 14 | 20 | 0.0200 | 0.2755 |
| 19 | 20 | 0.0159 | 0.0158 |
| 09 | 20 | 0.0155 | -0.0103 |
| 15 | 20 | 0.0113 | -0.2810 |

`desviacion_vs_global` es la diferencia relativa contra el MAE global de la ventana. La entidad con
peor desempeño es **14**, con MAE 0.0200
(+27.5% respecto al global).

Importa porque un error global aceptable puede esconder una entidad en la que el modelo funciona
mal, y las recomendaciones prescriptivas se emiten escuela por escuela.

## 4. Error contra cobertura de drivers

| tramo | escuelas | mae |
|---|---|---|
| ≤ 3 de 6 drivers | 3 | 0.0178 |
| 4-5 de 6 | 22 | 0.0152 |
| 6 de 6 | 55 | 0.0158 |

Responde la pregunta que el proyecto se hace explícitamente: **¿predecimos peor donde hay menos
datos?** Si el error crece al bajar la completitud, el sistema es menos confiable justo en las
zonas con cobertura parcial —y eso debe declararse junto a la predicción, no esconderse.

## 5. Umbrales de aceptación

`15_ML_Models/ML_Strategy` §5 fija: ML-02 F1 macro ≥ 0.6, ML-03 Silhouette
≥ 0.3.

Para ML-01 declara `MAE < 15 alumnos`, pero el contrato define el objetivo como
`target_variacion_matricula`, que es una **variación**, no un conteo. **Los umbrales de ML-01 no
son comparables con lo que reporta el pipeline** hasta fijar la unidad. Pendiente con Andrés
González Habib.

## 6. Cobertura de la evaluación

| Modelo | Estado |
|---|---|
| ML-01 · regresión | ✅ evaluado |
| ML-02 · clasificación | ✅ evaluado (target `driver_dominante_proxy`) |
| ML-03 · clustering | ⬜ **pendiente** — US-321 (Estefany Hernández), aún sin implementar |

AC-003.2 no queda cerrado hasta que ML-03 reporte su Silhouette.
