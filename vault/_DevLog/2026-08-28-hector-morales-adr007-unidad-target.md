---
project: "FARO"
date: "2026-08-28"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h"
touches: ["ADR-007", "BUG-017", "BUG-019", "US-104", "US-311", "US-313", "REQ-003"]
tags: [devlog, celula-3, ml, adr]
---

# DevLog — 2026-08-28 — La unidad del target no estaba en el contrato

→ [[vault/_DevLog/_index|Volver al índice]]

## Lo que confirmó Diana

`target_variacion_matricula = matricula_total - matricula_ciclo_anterior`. **Diferencia absoluta de
alumnos.** Si una escuela pasó de 500 a 480, el valor es `-20`.

Con eso, el MAE 10.90 son ~11 alumnos de error promedio. El modelo no estaba mal; lo que estaba mal
era publicarlo a través de una sigmoide calibrada sobre fracción.

## El defecto real no es de nadie

Miré mi propio código antes de opinar sobre el de C1, y ahí estaba lo importante:

| Productor | Grano | Fórmula | Unidad |
|---|---|---|---|
| `features_escuela.sql` (C1) | escuela | `matricula_total - matricula_ciclo_anterior` | alumnos |
| `target_hibrido.variacion_desde_serie` (yo) | municipio × nivel | `matricula_total / matricula_previa - 1.0` | fracción |

**Las dos escriben en la misma columna y las dos llegan a `gold.predicciones.valor`**, distinguidas
sólo por `grano` (DEC-010). Esa columna hoy mezcla alumnos con fracciones.

Y ninguno de los dos se equivocó contra lo escrito: `Data_Model.md` §5.3 declara `StrictFloat` y nada
más. **El contrato nunca dijo la unidad.** Es BUG-019, y es de fondo — no de C1.

## Por qué no es una preferencia de estilo

Diana preguntó a quién le toca decidir si se recalibra el riesgo sobre alumnos o se normaliza el
target a fracción. Antes de opinar quise ver si la evidencia inclinaba la balanza, y la inclina mucho.

El PRD pregunta "¿qué escuelas van a perder matrícula?" y el entregable las **ordena** por riesgo. Con
target absoluto, ese orden es aproximadamente un orden por tamaño de escuela:

| Escuela | Antes | Después | Absoluta | Fracción | Rank abs. | Rank frac. |
|---|---|---|---|---|---|---|
| Primaria rural | 48 | 29 | −19 | −39.6 % | 4.º | **1.º** |
| Secundaria urbana grande | 1 850 | 1 808 | −42 | −2.3 % | **1.º** | 4.º |

Sobre 4 000 escuelas simuladas: correlación entre `|variación absoluta|` y tamaño = **0.70**; entre
`|fracción|` y tamaño = **0.00**. Un modelo entrenado sobre diferencia absoluta aprende sobre todo a
predecir cuán grande es la escuela.

Lo que me convenció no fue la estadística sino su consecuencia: el sesgo empuja hacia abajo a las
escuelas pequeñas y rurales, que son exactamente las que "la escuela como sensor social" existe para
hacer visibles. Una telesecundaria que pierde 29 % de sus alumnos es señal de territorio; cuarenta
alumnos menos en un bachillerato de 2 400 es ruido. El target absoluto los ordena al revés.

## Lo que hice y lo que no

**Hice:** [[vault/03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula|ADR-007]] como
**propuesta**, con la evidencia y tres alternativas rechazadas con su razón. Registré BUG-019. Corregí
el mensaje de la guarda, que todavía adivinaba entre dos causas cuando ya sabemos cuál es.

**No hice:** cambiar mi `variacion_desde_serie` a alumnos, ni pedirle a C1 que cambie su SQL. La
unidad ganadora es decisión de equipo —toca Gold, modelos, API y tableros— y mi análisis es un insumo,
no el veredicto. ADR-003 ya había dejado la calibración pendiente de ratificar con Andrés y Christian;
esto entra por la misma puerta.

Sobre a quién le toca: Diana intuía que es charla de Andrés/Christian por ADR-003 y coincido, con la
corrección de que también la toca a ella (produce la columna) y que convocar es de Edgar como PO.

## Verificación

Suite **497 passed, 5 skipped**. Ruff y `vault_lint` limpios. La guarda sigue deteniendo la
publicación del grano escuela, que es lo correcto hasta que se ratifique la unidad.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `vault/03_Architecture/ADRs/ADR-007-*` (nuevo), `vault/03_Architecture/ADRs/_index.md`,
  `src/modelos/riesgo.py`, `vault/06_Quality_Testing/Bug_Register.md`,
  `vault/02_Requirements/Traceability_Matrix.md`
- **Decisiones autónomas del agente:**
  - Revisar mi propio código antes de opinar sobre el de C1 — de ahí salió BUG-019, que es el defecto
    de fondo y no estaba a la vista.
  - Cuantificar el sesgo en vez de argumentar por preferencia.
  - Escribir el ADR como `proposed` y no aplicar el cambio: la unidad la decide el equipo.
- **Correcciones manuales:** revisión línea por línea.

## Pendiente

1. **Ratificar ADR-007.** Bloquea que el `indice_riesgo` del grano escuela signifique algo.
2. Si se acepta: C1 normaliza y reprocesa, y hay que **regenerar las 45 249 filas** ya publicadas.
3. **BUG-018** con Andrés. **BUG-008** sigue `open`.
