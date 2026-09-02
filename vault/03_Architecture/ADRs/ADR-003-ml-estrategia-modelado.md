---
id: ADR-003
title: "ADR-003 — Estrategia de modelado ML: partición temporal, backtesting y cobertura parcial"
owner: "Andrés González Habib"
status: accepted
traces_up: ["REQ-003", "vault/02_Requirements/User_Stories"]
traces_down: ["vault/15_ML_Models/ML_Strategy", "US-301"]
supersedes: []
tags: [architecture, adr, ml, celula-3]
date: "2026-08-09"
---

# ADR-003 — Estrategia de modelado ML: partición temporal, backtesting y cobertura parcial

→ [[vault/03_Architecture/ADRs/_index|Volver a ADRs]]

## Contexto

FARO entrena 3 modelos sobre datos de matrícula escolar históricos (ciclos anuales SEP Formato 911).
Los datos tienen estructura de serie de tiempo: cada escuela tiene observaciones por ciclo.
Se deben tomar decisiones sobre cómo partir los datos, cómo evaluar los modelos antes de producción
y cómo manejar features de drivers con cobertura geográfica/temporal parcial (D5 agua, D6 aire).

## Decisión

Se adoptan tres protocolos no negociables para los 3 modelos (ML-01, ML-02, ML-03):

1. **Partición temporal obligatoria** — nunca aleatoria.
2. **Backtesting walk-forward de 1 ciclo** como protocolo estándar de evaluación.
3. **Estrategia explícita para cobertura parcial**: indicador binario + imputación de mediana de
   municipio; nunca cero, nunca nulo silencioso (alineado con AC-001.6).

## Alternativas consideradas

| Opción | Pros | Contras |
|---|---|---|
| Split aleatorio train/test | Sencillo, sklearn default | **Produce fuga de información**: el modelo ve datos futuros durante entrenamiento. Invalida métricas. Rechazada. |
| Partición temporal fija (último ciclo = test) | Sin fuga, simple | Un solo punto de evaluación. No detecta degradación del modelo a lo largo del tiempo. |
| **Walk-forward de 1 ciclo** ✅ | Sin fuga, múltiples puntos de evaluación, detecta drift temporal | Más costoso computacionalmente. Aceptable dado el volumen (4 entidades, ciclos anuales). |
| Eliminar filas con `SIN_DATO` | Simple | Pierde hasta 30% de escuelas (zonas sin datos de agua/aire). Sesgo geográfico. Rechazada. |
| Imputar con cero | Simple | Cero es dato válido (sin inseguridad = 0 delitos). Ambigüedad semántica. Rechazada. |
| **Indicador binario + mediana de municipio** ✅ | Preserva todas las escuelas; el modelo aprende cuándo el dato falta | Aumenta dimensionalidad (+1 feature por driver parcial). Aceptable. |

## Protocolo de partición temporal

```
Datos disponibles: ciclos 2013-14 · 2014-15 · … · 2023-24
──────────────────────────────────────────────────────────
Walk-forward de 1 ciclo:

  Fold 1: train=[2013-14 … 2019-20]  test=[2020-21]
  Fold 2: train=[2013-14 … 2020-21]  test=[2021-22]
  Fold 3: train=[2013-14 … 2021-22]  test=[2022-23]
  Fold 4: train=[2013-14 … 2022-23]  test=[2023-24]  ← fold de producción

Métrica reportada: promedio y desviación estándar de los 4 folds.
```

**Regla dura:** ningún dato de ciclo `t+1` aparece en el conjunto de entrenamiento del fold que
predice `t+1`. Verificado mediante test unitario (`TEST-ML-001`).

## Protocolo de backtesting por modelo

| Modelo | Métrica principal | Umbral mínimo aceptable | Métrica de alerta |
|---|---|---|---|
| ML-01 — Regresión de matrícula | MAE de variación relativa | MAE < 0.03 (3 puntos porcentuales) | RMSE < 0.05 (5 puntos porcentuales) |
| ML-02 — Clasificador de driver | F1 macro | F1 ≥ 0.60 | Precision por clase ≥ 0.50 |
| ML-03 — Clustering | Silhouette score | Silhouette ≥ 0.30 | Inercia estabilizada |

Los umbrales son **provisionales** (definidos sobre datos mock). Se revisarán al recibir
`gold.features_escuela` real (US-104, Diana Alvarez) y se actualizará este ADR si cambian.

Para ML-01, `target_variacion_matricula` es una proporción: `-0.05` representa una pérdida de 5 %.
Por ello, MAE y RMSE se reportan en puntos porcentuales. La alternativa de conservar umbrales en
alumnos se descartó porque el contrato de features no aporta la matrícula base necesaria para una
conversión reproducible. El límite de RMSE coincide con la variación de 5 % que activa el umbral de
riesgo; el MAE usa un límite más estricto de 3 puntos porcentuales.

## Protocolo de cobertura parcial (drivers D5 y D6)

Para cada driver con cobertura parcial, se generan **2 features** en el vector de entrada:

```python
# Ejemplo para D5 (estrés hídrico)
features["d5_estres_hidrico"]         = valor_real  | mediana_municipio_historica
features["d5_dato_disponible"]        = 1            | 0   # indicador de disponibilidad
```

Nunca se introduce un cero ni un nulo. El modelo aprende implícitamente cuándo el dato falta.
El campo `indice_completitud_drivers` (calculado por Célula 1) se incluye como feature adicional.

## Consecuencias

**Positivas:**
- Las métricas reportadas son realistas y defendibles ante el profesor.
- El sistema es honesto sobre la incertidumbre en zonas con cobertura parcial.
- El protocolo es reproducible y verificable con tests unitarios.

**Negativas:**
- Walk-forward requiere entrenar el modelo N veces (N = número de folds). Impacto bajo dado el
  tamaño del dataset (4 entidades, ~50 000 escuelas en scope).
- Aumenta la dimensionalidad con los indicadores binarios. Controlable con selección de features.

## Trazabilidad

- Requisito: REQ-003 (AC-003.3 partición temporal; AC-003.6 SHAP/prescriptivo)
- Impacta: [[vault/15_ML_Models/ML_Strategy]] · [[vault/03_Architecture/System_Design]]
- User Stories: US-301, US-302, US-303
- Tests: TEST-ML-001 (verificación de no-fuga temporal) — pendiente de implementar en US-301
