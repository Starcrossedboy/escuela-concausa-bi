---
id: ADR-007
title: "ADR-007 — Unidad de target_variacion_matricula: fracción, no diferencia absoluta"
owner: "Héctor Rafael Morales Marbán"
status: proposed
traces_up: ["REQ-003", "ADR-003"]
traces_down: ["US-104", "US-311", "US-313", "15_ML_Models/Indice_Riesgo_ML01", "03_Architecture/Data_Model"]
supersedes: []
tags: [architecture, adr, ml, celula-1, celula-3, celula-4]
date: "2026-08-28"
---

# ADR-007 — Unidad de `target_variacion_matricula`: fracción, no diferencia absoluta

> **Estatus: propuesta.** Requiere ratificación de Andrés González Habib (ADR-003, modelado),
> Christian Ruiz (contrato de la API) y Diana Alvarez (producción en Gold). Convoca: Edgar Coronel.

## Contexto

El contrato nunca dijo en qué unidad se expresa `target_variacion_matricula`. `Data_Model.md` §5.3 lo
declara `StrictFloat` y nada más. Con esa ambigüedad, los dos productores eligieron distinto:

| Productor | Grano | Fórmula | Unidad |
|---|---|---|---|
| `dbt/models/gold/features_escuela.sql` (C1, US-104) | escuela | `matricula_total - matricula_ciclo_anterior` | **alumnos** |
| `src/modelos/target_hibrido.variacion_desde_serie` (C3, DEC-007) | municipio × nivel | `matricula_total / matricula_previa - 1.0` | **fracción** |

Ambos escriben en la misma columna y ambos alimentan `gold.predicciones.valor`, distinguidos sólo por
`grano` (DEC-010). Hoy esa columna **mezcla alumnos y fracciones**.

Se descubrió el 2026-08-28, cuando la primera corrida real de ML-01 reportó `MAE 10.90` y la guarda de
escala de `verificar_escala_variacion()` detuvo la publicación (BUG-017). Diana confirmó la fórmula de
C1 en el SQL. El `indice_riesgo` está calibrado sobre fracción (`-0.05` = "pierde 5 % de su
matrícula"), calibración que ADR-003 dejó explícitamente pendiente de ratificar.

## Decisión propuesta

**`target_variacion_matricula` se expresa como fracción del ciclo anterior**:
`matricula_total / matricula_previa - 1.0`. La unidad se declara en el contrato.

C1 normaliza en `features_escuela.sql`. La calibración de `indice_riesgo` **no cambia**.

## Por qué no es una preferencia de estilo

La diferencia absoluta responde una pregunta distinta a la del proyecto. El PRD pregunta *"¿qué
escuelas van a perder matrícula?"*, y el entregable las **ordena** por riesgo. Con target absoluto,
ese orden es aproximadamente un orden por tamaño de escuela.

Mismos datos, dos targets:

| Escuela | Antes | Después | Absoluta | Fracción | Rank abs. | Rank frac. |
|---|---|---|---|---|---|---|
| Primaria rural | 48 | 29 | −19 | −39.6 % | 4.º | **1.º** |
| Telesecundaria rural | 62 | 44 | −18 | −29.0 % | 5.º | 2.º |
| Primaria urbana media | 420 | 398 | −22 | −5.2 % | 3.º | 3.º |
| Secundaria urbana grande | 1 850 | 1 808 | −42 | −2.3 % | **1.º** | 4.º |
| Bachillerato metropolitano | 2 400 | 2 360 | −40 | −1.7 % | 2.º | 5.º |

**El orden se invierte.** Con target absoluto, la escuela más urgente del país sería la secundaria
grande que perdió 2.3 % de su matrícula, y la primaria rural que perdió casi 40 % quedaría en cuarto
lugar.

Sobre 4 000 escuelas simuladas con distribución de tamaños realista:

- correlación entre `|variación absoluta|` y tamaño de escuela: **0.70**
- correlación entre `|fracción|` y tamaño de escuela: **0.00**

Un modelo entrenado sobre diferencia absoluta aprende sobre todo a predecir **cuán grande es la
escuela**, no cuán en riesgo está.

### La consecuencia que importa para este proyecto

El sesgo no es neutro: empuja sistemáticamente hacia abajo a las escuelas pequeñas y rurales, que son
exactamente las que "la escuela como sensor social" existe para hacer visibles. Una telesecundaria que
pierde un tercio de sus alumnos es una señal de territorio; cuarenta alumnos menos en un bachillerato
metropolitano de 2 400 es ruido estadístico. El target absoluto los ordena al revés.

## Alternativas consideradas

**A. Recalibrar `indice_riesgo` sobre alumnos absolutos.** Rechazada: no existe un umbral absoluto que
signifique "en riesgo" para escuelas de 48 y de 2 400 alumnos a la vez. Cualquier constante elegida es
arbitraria para una de las dos, y el problema del orden por tamaño persiste intacto.

**B. Dejar ambas unidades y convertir en la API.** Rechazada: mueve la ambigüedad a C4 y deja
`gold.predicciones.valor` sin significado propio. Un tablero que lea Gold directo —que es justo lo que
hace Superset— seguiría mezclando.

**C. Normalizar en C3 al leer, sin tocar Gold.** Rechazada: dejaría a `gold.features_escuela` como
fuente con unidad implícita, y cualquier otro consumidor repetiría el error.

## Consecuencias

- C1 cambia una línea de `features_escuela.sql` y **reprocesa** Gold.
- Las 45 249 filas ya publicadas en `gold.predicciones` deben regenerarse: su `indice_riesgo` está
  saturado y no significa nada.
- `Data_Model.md` §5.3 y `src/modelos/contrato.py` declaran la unidad explícitamente (Diana ya lo
  ofreció).
- ML-01 hay que reentrenarlo; el MAE dejará de leerse en alumnos y pasará a leerse en fracción, lo que
  además lo vuelve comparable entre entidades de tamaños distintos.
- `matricula_previa == 0` deja de ser divisible. `variacion_desde_serie` ya rechaza ese caso de forma
  explícita; C1 necesita la misma regla, no un `NULLIF` silencioso que produzca `SIN_DATO` invisible.

## Qué pasa si no se decide

`verificar_escala_variacion()` seguirá deteniendo la publicación, que es el comportamiento correcto
pero deja el tramo ML → Gold bloqueado para el ensayo E2E.
