---
project: "FARO"
date: "2026-08-27"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1h"
touches: ["BUG-015", "BUG-013", "US-311", "US-313", "REQ-003", "TEST-005"]
tags: [devlog, celula-3, ml, bug]
---

# DevLog — 2026-08-27 — BUG-015, segunda vuelta: la cobertura se mira por ventana

→ [[_DevLog/_index|Volver al índice]]

## Qué falló de mi primer arreglo

Diana confirmó que la conexión y el cálculo automático de ventanas ya salían bien —reportaba 5 de 6
drivers y 1 ventana, como se esperaba— **pero el entrenamiento seguía tronando con el mismo error**.

Mi arreglo excluía los drivers vacíos **en todo el conjunto**. La exclusión correcta es **dentro de
la ventana de entrenamiento**.

Un driver puede tener datos globalmente y estar entero en `NaN` en el tramo con el que se entrena.
Es exactamente **D6 (aire)**: llega por la interpolación IDW de US-105 y sólo cubre el ciclo más
reciente, que con 3 ciclos y 1 ventana cae del lado de **prueba**, no del de entrenamiento. Con la
comprobación global, D6 pasaba el filtro y volvía a romper el binning.

Reproducido antes de corregir, igual que la vez pasada:

```
drivers utilizables GLOBALMENTE: [d1, d2, d3, d4, d6]
  ventana entrena[2021-2022…2022-2023] -> prueba[2023-2024]
    utilizables DENTRO del entrenamiento: [d1, d2, d3, d4]
❌ ValueError: window shape cannot be larger than input array shape
```

## La corrección

La cobertura se evalúa **por ventana**, y los dos casos se reportan por separado porque son
situaciones distintas:

```
⚠️  Drivers sin ningún dato en todo el conjunto: ['d5_agua']. Quedan fuera del modelo.
⚠️  entrena[2021-2022…2022-2023] -> prueba[2023-2024]: sin datos en el entrenamiento
    ['d5_agua', 'd6_aire']; se entrena con 4 de 6 drivers.
```

Un driver que **no existe nunca** (D5, DS-06 sin descarga) no es lo mismo que uno que **aún no cubre
el pasado** (D6, interpolado sólo para el ciclo reciente). El primero es un hueco de fuente; el
segundo se resuelve solo cuando haya más ciclos interpolados.

Si una ventana se queda sin ningún driver, falla nombrando **cuál** ventana.

## Lo que aprendí de mis dos intentos

El primer arreglo lo verifiqué contra un escenario que **yo mismo construí**: puse un driver en
`NaN` en todo el conjunto. Pasó, y lo di por bueno. Pero el escenario real era otro, y no lo
descubrí porque **no reproduje la forma real de los datos de Diana**, sólo la que yo suponía.

La lección concreta: cuando alguien reporta un fallo con datos que no tengo, la simulación tiene que
imitar **la estructura de sus datos**, no la del defecto que yo imagino. La segunda vez simulé D6
cubriendo sólo el ciclo reciente —como la IDW real— y el fallo apareció de inmediato.

## Verificación

```
⚠️  ... se entrena con 4 de 6 drivers.
drivers usados: ['d1_pobreza', 'd2_inseguridad', 'd3_infraestructura', 'd4_conectividad']
MAE 0.0187 · mejora sobre baseline 33.7%
✅ corre
```

**2 pruebas nuevas**, una de ellas la regresión exacta de este caso: un driver con datos globales
pero vacío en la ventana. Suite: **480 passed, 5 skipped**.

> **Sigue sin verificarse contra los datos reales.** Su ambiente es el único con Gold materializada.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `src/modelos/entrenar_ml01.py`, `tests/test_entrenar_ml01.py`,
  `06_Quality_Testing/Bug_Register.md`
- **Decisiones autónomas del agente:**
  - Reproducir el escenario imitando la **estructura de los datos reales** (D6 sólo en el ciclo
    reciente) en vez de la forma del defecto supuesto.
  - Separar los dos mensajes: "sin datos nunca" y "sin datos en esta ventana" tienen causas y
    dueños distintos.
  - Nombrar la ventana en el error, no sólo decir que faltan datos.
- **Correcciones manuales:** revisión línea por línea. Se dejó registrado en el DevLog por qué el
  primer arreglo no bastó, en vez de sólo corregirlo.

## Pendiente

1. **Que Diana repita la corrida.** Es el tercer intento; si vuelve a fallar, conviene que me
   comparta una muestra anonimizada de `gold.features_escuela` para dejar de trabajar a ciegas.
2. **BUG-008** sigue `open`. El ensayo es mañana.
