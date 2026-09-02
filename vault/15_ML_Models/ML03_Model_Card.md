---
id: DOC-ML03-CARD
title: "Ficha de Modelo: ML-03 (Clustering de Escuelas)"
owner: "Carlos Guillermo Mayorga Tapia"
status: in_review
source_of_truth: false
traces_up: ["US-324"]
tags: [ml, ml-03, clustering, no-supervisado, model-card]
---

# Ficha de Modelo: ML-03 (Clustering de Escuelas)

> → [[vault/15_ML_Models/_index|Volver a _index]]

## 1. Propósito
El objetivo de **ML-03** es un agrupamiento no supervisado (clustering) para encontrar perfiles similares de escuelas. Se utiliza para identificar bolsas de escuelas con problemáticas comunes independientemente de su región geográfica o su índice de riesgo directo de ML-01. (Ver: [[vault/15_ML_Models/ML_Strategy]]).

## 2. Features de Entrada
- **Features Propuestas:** Múltiples indicadores sociodemográficos, de infraestructura y académicos.
- **Features Efectivamente Implementadas:** Subconjunto robusto de características de `gold.features_escuela` excluyendo columnas fuertemente esparsas.
- Variables normalizadas/estandarizadas para evitar sesgos por escalas (ej. matrícula absoluta vs. índices porcentuales).

## 3. Métrica Obtenida
- **Métrica principal**: Coeficiente de **Silhouette** (Silhouette Score).
- **Resultados actuales**: **Pendiente de entrenamiento; todavía no hay Silhouette obtenido** (ya que la historia US-321 sigue pendiente de implementación).

## 4. Limitaciones Conocidas
- Carece de una "verdad absoluta" al ser no supervisado; los clústeres resultantes requieren interpretación y etiquetado de negocio (ej. "Escuelas rurales sin conectividad", "Escuelas urbanas saturadas").
- Sensible a la maldición de la dimensionalidad si se introducen demasiadas features sin una previa selección o PCA.

## 5. Contextos de NO Uso
- **NO usar para estimar series de tiempo** (ej. proyectar matrículas a futuro). Para eso existe ML-01.
- **NO usar para clasificar directamente el riesgo de un alumno**. Los clústeres agrupan condiciones estructurales, no el destino final de un estudiante individual.
