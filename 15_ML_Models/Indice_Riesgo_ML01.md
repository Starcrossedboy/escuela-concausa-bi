---
id: DOC-INDICE-RIESGO
title: "Índice de riesgo de ML-01 — de variación de matrícula a [0,1]"
owner: "Héctor Rafael Morales Marbán"
status: in_review
traces_up: ["02_Requirements/User_Stories", "03_Architecture/Data_Model", "15_ML_Models/ML_Strategy"]
traces_down: ["US-311", "US-313"]
tags: [ml, celula-3, ml-01, contrato]
---

# Índice de riesgo de ML-01 — de variación de matrícula a [0,1]

> Define cómo la predicción de ML-01 se convierte en el `indice_riesgo` que consumen la API, los
> cubos de Superset y FARO Web. **Propuesta pendiente de ratificar** con Andrés González Habib
> (ADR-003) y Christian Ruiz (contrato de la API).
> → [[15_ML_Models/_index]] · [[15_ML_Models/ML_Strategy]] · [[03_Architecture/Data_Model]]

## 1. El hueco que cierra

ML-01 predice `target_variacion_matricula`: un float **con signo y sin cota**, la variación de
matrícula respecto al ciclo anterior. Negativo significa que la escuela pierde alumnos.

Pero todo aguas abajo espera un número **acotado a [0,1]**, donde más alto = más riesgo:

| Consumidor | Qué espera | Dónde |
|---|---|---|
| API de inferencia | `indice_riesgo: float` con `Field(ge=0, le=1)` | `src/api/schemas.py::PrediccionOut` (US-401) |
| Almacén Gold | `valor` de `gold.predicciones` con `modelo = 'ML-01'` | [[03_Architecture/Data_Model]] §4.5 |
| Tableros | cuenta "escuelas en riesgo" con `indice_riesgo >= 0.6` | [[04_UX_Design/Screen_Specs]] |

La conversión entre ambas cosas **no estaba definida en ningún lado**. Este documento y
`src/modelos/riesgo.py` la fijan en un solo lugar, para que los tres consumidores lean el mismo
número.

## 2. La definición

Una **sigmoide monótona decreciente** en la variación, determinada por dos anclas de negocio:

| Variación de matrícula | `indice_riesgo` | Lectura |
|---|---|---|
| `0.00` — matrícula estable | **0.30** | riesgo bajo, no nulo |
| `-0.05` — pierde 5 % | **0.60** | exactamente el umbral de "escuela en riesgo" de los tableros |

```
indice_riesgo(v) = expit((centro - v) / escala)

con centro y escala despejados de las dos anclas:
   centro = -0.033817     escala = 0.039912
```

Las constantes **no se escriben a mano**: se derivan de las anclas en tiempo de importación. Mover
una ancla recalibra todo el sistema de forma consistente y sin tocar el código que la consume.

### Valores de referencia

| Variación | Riesgo | Interpretación |
|---|---|---|
| `+0.10` | 0.09 | crece 10 %: riesgo mínimo |
| `0.00` | 0.30 | estable |
| `-0.05` | 0.60 | umbral de alerta |
| `-0.10` | 0.84 | pierde 10 %: alerta alta |
| `-0.20` | 0.99 | colapso de matrícula |

## 3. Por qué una sigmoide

| Alternativa | Por qué se descartó |
|---|---|
| **Min-max** sobre el conjunto | El índice cambia si entra una escuela atípica, y no es comparable entre ciclos. Una escuela idéntica saldría con riesgo distinto según con quién la midan. |
| **Percentil (ECDF)** | Es relativo: si un año caen todas las escuelas, la mitad seguiría saliendo con riesgo bajo. Pésima propiedad para un sistema de alerta temprana. |
| **Sigmoide** ✅ | **Absoluta y estable**: la misma variación produce siempre el mismo riesgo, sin importar el resto del universo ni el ciclo. Acotada por construcción, así que nunca viola el contrato de la API. Monótona, así que el orden de las escuelas se preserva. |

La monotonía importa además porque la métrica reportada de ML-01 sigue siendo **MAE/RMSE sobre la
variación** (AC-003.2). El índice es una capa de presentación: no cambia el modelo, no cambia la
métrica y no se entrena contra él.

## 4. Lo que hay que ratificar

Lo discutible son **las anclas**, no la forma funcional:

1. **¿`0.30` es el riesgo correcto para una escuela estable?** Se eligió distinto de cero porque
   ninguna escuela tiene riesgo nulo, pero es un juicio de negocio.
2. **¿`-5 %` es el umbral de "escuela en riesgo"?** Se tomó del `0.6` que ya usan los tableros de
   [[04_UX_Design/Screen_Specs]], leyéndolo al revés. Conviene que Manuel lo confirme.
3. **¿El `indice_riesgo` de `gold.predicciones` es este, o la variación cruda?** El `Data_Model`
   §4.5 declara `valor` genérico. Propongo guardar **ambos**: la variación en `valor` y el índice
   como columna derivada, para no perder la unidad original.

## 5. Pruebas

`tests/test_riesgo.py` — 16 casos. Los que importan:

- `test_reproduce_el_ancla_del_umbral_de_negocio` — perder 5 % cae exactamente en 0.60.
- `test_esta_acotada_incluso_en_extremos` — ni con ±1e6 se sale de [0,1].
- `test_cumple_el_contrato_de_la_api` — construye un `PrediccionOut` real de la Célula 4 con el
  valor calculado. Si alguien recalibra fuera de rango, el CI lo detiene antes de que falle la API.
- `test_la_inversa_traduce_el_umbral_del_tablero` — permite explicar un número del tablero en
  lenguaje de negocio: "riesgo 0.60 = perder 5 % de matrícula".
