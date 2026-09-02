---
project: "FARO"
date: "2026-08-27"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "2h"
touches: ["BUG-015", "BUG-013", "US-311", "US-313", "REQ-003", "TEST-005", "TEST-003"]
tags: [devlog, celula-3, ml, bug]
---

# DevLog — 2026-08-27 — BUG-015: un driver sin datos impedía entrenar sobre el Gold real

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué pasó

Diana corrió `publicar_gold --desde-gold` sobre `gold.features_escuela` real y me pasó el traceback.
**La lectura funcionó** —135 932 filas, 46 515 escuelas, ciclos 2022-2023 a 2024-2025—, así que el
`--desde-gold` del PR #109 hace su trabajo. Pero el entrenamiento tronó:

```
ValueError: window shape cannot be larger than input array shape
  en sklearn/.../binning.py::_find_binning_thresholds
```

No se publicó nada: falla antes de escribir a Gold.

## Diagnóstico

Reproduje el fallo de forma aislada antes de tocar nada, para no adivinar la causa:

| Caso | Resultado |
|---|---|
| Columna **toda `NaN`** (driver 100 % `SIN_DATO`) | ❌ falla exactamente igual |
| Columna **constante** | ✅ entrena sin problema |

`HistGradientBoostingRegressor` calcula sus cortes con `sliding_window_view(distinct_values, 2)`.
Sin ningún valor distinto, la ventana de tamaño 2 no cabe y numpy falla con un mensaje **que no
menciona la causa real**.

En el Gold real el driver es **D5 (agua)**: sigue completo en `SIN_DATO` porque DS-06 (CONAGUA) no
tiene descarga verificada. **El fixture nunca lo ejercitó** porque su generador siempre da algún
valor a los seis drivers — un punto ciego de mi propio dato de prueba.

## Corrección

`drivers_utilizables()` detecta los drivers con al menos un valor observado y los excluye del
entrenamiento **reportándolo**:

```
⚠️  Drivers sin ningún dato, excluidos del entrenamiento: ['d5_agua'].
    Se entrena con 5 de 6.
```

Que un driver no aporte nada **es un hallazgo del proyecto**, no un detalle de implementación. Por
eso `ResultadoEntrenamiento` expone `drivers_usados` y `drivers_excluidos`: la exclusión tiene que
llegar al reporte de US-312 y a MLflow, no quedarse en un print.

Si **ningún** driver tiene datos, falla con un mensaje explícito en vez de un error de numpy.

`construir_predicciones` toma ahora las columnas de `feature_names_in_` del modelo: pasarle los seis
drivers a un modelo entrenado con cinco habría fallado por desajuste de forma al predecir.

## Segundo hallazgo, también de Diana

El default `--ventanas 3` exigía 5 ciclos y el Gold real tiene 3 utilizables — 2021-2022 se consume
como referencia del target. Tenía razón: un default fijo no puede servir para el fixture (5 ciclos)
y para el Gold real (3) a la vez.

`--ventanas` pasa a ser **automático**: `ventanas_posibles()` calcula el máximo que permiten los
ciclos disponibles y lo reporta. El fixture da 3, el Gold real da 1.

## Verificación

Simulé el escenario exacto —3 ciclos y D5 en `SIN_DATO`— y el circuito completo corre:

```
ciclos: ['2022-2023', '2023-2024', '2024-2025'] · filas: 240
ventanas automáticas: 1
⚠️  Drivers sin ningún dato, excluidos: ['d5_agua']. Se entrena con 5 de 6.
predicciones construidas: 80 filas del ciclo 2024-2025
```

**9 pruebas nuevas**, entre ellas una que reproduce el caso de Diana. Suite: **478 passed**.

> **Lo que sigue sin verificarse:** la corrida contra los datos reales. Falta que Diana la repita
> con este arreglo — su ambiente es el único con Gold materializada.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/entrenar_ml01.py`, `src/modelos/particion_temporal.py`,
  `src/modelos/publicar_gold.py`, `tests/test_entrenar_ml01.py`,
  `tests/test_particion_temporal.py`, `vault/06_Quality_Testing/Bug_Register.md`
- **Decisiones autónomas del agente:**
  - Reproducir el fallo aislado antes de corregir, para distinguir "sin datos" de "sin varianza":
    resultaron ser casos distintos y sólo el primero rompe.
  - Excluir el driver **reportándolo** y exponerlo en el resultado, en vez de filtrarlo en silencio.
  - Tomar las columnas de `feature_names_in_` al predecir, para que el modelo y la predicción no
    puedan desalinearse.
  - Hacer `--ventanas` automático en vez de subir el default: cualquier número fijo se rompe con
    otro conjunto de ciclos.
- **Correcciones manuales:** revisión línea por línea; se verificó que el escenario de Diana corre
  de punta a punta antes de dar el arreglo por bueno.

## Pendiente

1. **Que Diana repita la corrida** con este arreglo. Si pasa, `gold.predicciones` y
   `gold.recomendaciones` quedan con datos reales y el `JOIN` de DB-03 deja de dar cero (BUG-013).
2. **Con 3 ciclos sólo hay 1 ventana de backtesting.** ADR-003 pide 4. Con el 4.º ciclo de Diana
   (2021-2022, hoy consumido como referencia) subiría a 2. Conviene decirlo antes de comprometer
   métricas.
3. **BUG-008** sigue `open`. El ensayo es mañana.
