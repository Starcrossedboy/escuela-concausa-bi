---
project: "FARO"
date: "2026-08-27"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h30"
touches: ["BUG-016", "BUG-017", "BUG-018", "US-311", "US-313", "REQ-003", "TEST-004", "TEST-006"]
tags: [devlog, celula-3, ml, bug]
---

# DevLog — 2026-08-27 — ML-01 corrió contra Gold real; tres hallazgos nuevos

→ [[_DevLog/_index|Volver al índice]]

## Lo que sí funcionó

Diana confirmó que el arreglo de [[_DevLog/2026-08-27-hector-morales-bug015-segunda-vuelta|BUG-015]]
sirvió: **ML-01 entrenó y publicó contra la Gold real**, 45 249 filas en `gold.predicciones`, y los
avisos de D5/D6 salieron como se describieron. Es la primera vez que el tramo ML → Gold corre con
datos de verdad.

## BUG-016 — filas con los 6 drivers en NULL

El fallo que reportó: hay escuelas sin **ningún** driver observado, y
`generar_driver_dominante_proxy` truena ahí por diseño. Hace bien: no se puede nombrar un driver
dominante donde no se observó ninguno.

Lo que faltaba era apartarlas antes. C1 ya adoptó esa convención en la `driver_dominante` real de
US-302 (PR #113) dejándolas en `NULL`, y Diana me lo señaló como referencia. Como
`validar_target_ml02` rechaza nulos, el filtrado va en el sitio de llamada, que es mío.

Conservan su predicción de ML-01 —la variación no necesita drivers— y no reciben recomendación.
`SIN_DATO` explícito, nunca un driver inventado.

### Lo que encontró la simulación y no las pruebas unitarias

Al apartar filas de `features_ml02`, esas escuelas quedan con predicción pero sin features y
`construir_recomendaciones_ml02` lo rechaza. La salida fácil era relajar esa verificación; hice lo
contrario: filtro las predicciones en el sitio de llamada y la verificación queda intacta, porque
debe seguir cazando desajustes de verdad y no el hueco que abrí a propósito. Hay una prueba que lo
fija.

Vale la pena anotarlo: **mis pruebas unitarias pasaban y el flujo completo no**. Sólo apareció al
simular la corrida entera de Diana de punta a punta. Es la segunda vez en dos días que reproducir la
forma real del flujo encuentra lo que las pruebas aisladas no.

## BUG-017 — el número que no me cuadró

Diana reportó **MAE 10.90** como quien reporta buenas noticias, y ahí está el problema. La sigmoide
de `indice_riesgo` está calibrada sobre **fracción**: `-0.05` significa "pierde 5 % de su matrícula"
→ riesgo 0.60. Un error medio de 10.90 es **218 veces** la banda completa de calibración.

Verificado: con esa escala, las 45 249 filas publicadas quedan en riesgo ≈ 1.00. No es salida
degradada, es salida **incorrecta que se ve normal**: el tablero contaría como "en riesgo" a todo el
universo y nadie lo notaría mirando la pantalla.

La sospecha es que `target_variacion_matricula` viene en puntos porcentuales o como diferencia
absoluta de alumnos. `verificar_escala_variacion()` ahora detiene la publicación antes de convertir.
Mira la **mediana** de `|variación|`, no el máximo: una escuela que triplica matrícula es legítima,
una columna entera en otra escala no.

**Falta lo que no me toca:** confirmar con C1 las unidades de US-104. Si la escala es correcta y el
dato es así, hay que recalibrar las anclas — pero eso es decisión de negocio, no arreglo de código.

## BUG-018 — ML-02 repite el defecto de BUG-015

Al simular la corrida completa apareció el siguiente muro, que Diana todavía no ha visto:
`entrenar_ml02._matriz()` toma siempre los seis drivers sin comprobar cobertura dentro de la ventana.
Es **el mismo defecto** que ya arreglé en ML-01, en el clasificador, y se dispara con el mismo D6.

`entrenar_ml02.py` es de Andrés. **No lo toqué.** Dejé la reproducción y el parche preparado para que
lo aplique él; la regla del repo es no trabajar fuera del alcance ajeno, y un arreglo mío en su
módulo le llegaría como sorpresa en medio de su propio avance.

## Verificación

```
✅ ML-01: MAE 0.0177 · 80 predicciones (incluye las filas sin drivers)
⚠️  apartadas de ML-02: 40
✅ guarda de escala: detiene con -10.9
```

**11 pruebas nuevas.** Suite: **492 passed, 5 skipped**. Ruff y `vault_lint` limpios.

Nota aparte: descubrí que **los doctests no corren en el CI** —no hay configuración de pytest en el
repo, y la suite se invoca como `pytest tests/ -q`. Verifiqué que el doctest nuevo no fuera vacuo
rompiéndolo a propósito, pero la cobertura real la dan las pruebas de `tests/`, no los ejemplos del
docstring. Conviene decidirlo en equipo.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/publicar_gold.py`, `src/modelos/riesgo.py`,
  `tests/test_publicar_gold.py`, `tests/test_riesgo.py`, `06_Quality_Testing/Bug_Register.md`,
  `02_Requirements/Traceability_Matrix.md`
- **Decisiones autónomas del agente:**
  - No relajar la verificación de sincronía de `construir_recomendaciones_ml02`; filtrar en el
    sitio de llamada y dejarla vigilando.
  - Detener la publicación ante escala sospechosa en vez de advertir: un `indice_riesgo` saturado
    no se ve roto en un tablero, y eso es justamente lo peligroso.
  - Usar la mediana y no el máximo para juzgar la escala.
  - **No tocar `entrenar_ml02.py`** pese a tener el arreglo listo, por ser de otro dueño.
- **Correcciones manuales:** revisión línea por línea.

## Pendiente

1. **Confirmar unidades de `target_variacion_matricula` con C1** (BUG-017). Bloquea que el
   `indice_riesgo` publicado signifique algo.
2. **Pasarle BUG-018 a Andrés** con el parche.
3. **BUG-008** sigue `open`. El ensayo es mañana.
