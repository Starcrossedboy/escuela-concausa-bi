---
id: DOC-EDA-FEATURES-US322
title: "US-322 — EDA y selección de variables para ML-03"
owner: "Estefany Lucero Hernández Loredo"
status: in_review
traces_up: ["US-322", "REQ-003", "15_ML_Models/ML_Strategy"]
traces_down: ["US-321"]
tags: [ml, eda, features, celula-3]
---

# US-322 — EDA y selección de variables para ML-03

> Implementación reproducible: `src/modelos/analizar_features.py`.

## Alcance

El diagnóstico valida el contrato de `gold.features_escuela` sobre el fixture sintético y reporta:

- Nulos, cardinalidad y correlación de los seis drivers y `indice_completitud_drivers`.
- Matriz de correlaciones de las features; el target no se mezcla con las variables de clustering.
- Llaves y target excluidos del vector: `cct`, `id_ciclo` y `target_variacion_matricula`.
- Coherencia obligatoria entre valores ausentes y la bandera `SIN_DATO`.

## Selección inicial para ML-03

Las candidatas son los seis drivers, `indice_completitud_drivers` y los indicadores de disponibilidad
de D5/D6. La imputación se ajustará solamente con cada conjunto de entrenamiento; nunca se usará
cero para cubrir una ausencia.

## Limitación conocida

El fixture tiene 400 observaciones sintéticas de 80 escuelas y 5 ciclos. Sirve para verificar el
pipeline, no para declarar perfiles de negocio o resultados sobre escuelas reales.

## Criterio de salida

US-321 puede consumir estas variables solo después de revisar correlaciones, cobertura y la decisión
de Célula 1 sobre `cve_mun` para la imputación establecida en ADR-003.
