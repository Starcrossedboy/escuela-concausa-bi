---
project: "FARO"
date: "2026-08-28"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude"
model: "sonnet-5"
session_duration: "~2h"
touches: ["US-302", "US-104"]
tags: [devlog, gold, dbt, ml, us302, driver_dominante, contrato]
---

# US-302 — `driver_dominante` real en `gold.features_escuela`

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

**1. Columna `driver_dominante` en `gold.features_escuela`.** Andrés González Habib (C3) pidió en
`vault/15_ML_Models/Preguntas_Coordinacion_C3.md` que Célula 1 publicara una etiqueta real para entrenar
ML-02 (hasta hoy solo existía `driver_dominante_proxy` en `entrenar_ml02.py`). Coordinado con él
por mensaje, dio luz verde con especificación completa (2026-08-28): argmax entre drivers con
`*_cobertura = 'OK'`, desempate determinista D1>D2>D3>D4>D5>D6, `NULL` (nunca un valor artificial)
cuando ninguna fila tiene driver elegible, documentada explícitamente como etiqueta **operativa**,
no observación causal.

Implementado en una nueva CTE (`con_driver_dominante`) usando `lateral join` sobre
`unnest(array[códigos], array[valores])`, filtrando a `cobertura = 'OK'` y ordenando por
`valor desc, código asc` — el orden lexicográfico de 'D1'..'D6' resuelve el desempate por
prioridad sin lógica adicional.

**2. Es la MISMA regla que ya vivía en Python** (`generar_driver_dominante_proxy()` en
`entrenar_ml02.py`, de Andrés/Héctor) — se centraliza en Gold, no se inventa una regla nueva.
Agregada una prueba de paridad (`tests/test_entrenar_ml02.py::test_paridad_driver_dominante_real_contra_proxy`)
que compara la columna real contra el proxy fila por fila.

**3. Cinco pruebas dbt nuevas** (`dbt/tests/features_escuela_driver_dominante_*.sql`): el driver
elegido siempre tiene cobertura OK (nunca SIN_DATO), el valor elegido es efectivamente el máximo
entre los elegibles (no solo "cualquiera" con cobertura OK), nunca queda NULL si hay al menos un
driver elegible, no rompe el grano `cct × id_ciclo`, y un caso sintético de desempate (con
empates armados a propósito, ya que no hay garantía de que el fixture real produzca uno) que
reproduce la regla exacta de la CTE y verifica que gana el driver de mayor prioridad.

**4. Contrato Python actualizado.** `src/modelos/contrato.py`: nuevo enum `DriverDominante`
(D1..D6) y campo `driver_dominante: DriverDominante | None` en `FeaturesEscuela`. Espejo en
`vault/03_Architecture/Data_Model.md` §5.3 actualizado con la misma nota aclaratoria: este
`driver_dominante` (etiqueta de entrenamiento, en `gold.features_escuela`) **no es el mismo dato**
que el `driver_dominante` de `gold.recomendaciones` (predicción del modelo ya entrenado, servida
por inferencia) — misma regla de argmax, dos momentos distintos del pipeline.

**5. Fixture regenerado.** `src/modelos/generar_fixture.py` ahora calcula `driver_dominante` con
la misma regla (antes solo sesgaba los datos para que hubiera un driver dominante "de facto", sin
publicarlo). Regenerado `tests/fixtures/features_escuela_mock.csv` (400 filas, 17 columnas,
validadas 400/400 contra el contrato).

**6. Efecto esperado sobre las pruebas de C3 (no corregido, es de ellos):** con `driver_dominante`
real en el fixture, `cargar_features_ml02()` deja de usar el proxy automáticamente (por diseño,
`columna_target_disponible()` prefiere el real) — esto cambia las métricas de ML-02 que reporta
`vault/06_Quality_Testing/Automated/Evaluacion_Modelos.md` (dueño: Héctor Morales Marbán). Ese archivo
dice explícitamente "se regenera cuando la Célula 1 publique `gold.features_escuela`" — así que
`tests/test_evaluar.py::test_el_reporte_publicado_esta_sincronizado` queda fallando a propósito
hasta que Héctor corra `python -m src.modelos.evaluar` y republique. No se tocó ese archivo.

Sí se corrigió `tests/test_entrenar_ml02.py::test_carga_fixture_y_agrega_target_proxy`: probaba
la rama "sin etiqueta real" contra el fixture por defecto, que ahora sí trae la etiqueta real. Se
ajustó para probar contra una copia del fixture sin esa columna — mismo comportamiento cubierto,
ya no depende de que el fixture por defecto carezca de la columna.

## Cómo se probó

```
python -m pytest tests/ -q                          # 467 passed, 5 skipped, 1 failed (conocido, ver punto 6)
cd dbt && dbt build --select features_escuela --target dev   # 17/17 (1 modelo + 16 tests)
cd dbt && dbt build --target dev                     # 173 passed, 19 errores (conocidos, gold.recomendaciones
                                                        # aún no publicada por publicar_gold.py en este ambiente)
python vault/_Meta/scripts/vault_lint.py .                 # Vault limpio
```

## Avance entregado

- `US-302`: Célula 1 publica `driver_dominante` real, acordado con C3. No cierra la historia
  (es de Andrés) — es la evidencia/columna que él pidió para poder entrenar y medir sin proxy.
- Falta: abrir PR (cambio de contrato compartido, PM como aprobador obligatorio por pedido de
  Andrés), avisar a Andrés/Héctor cuando esté la rama para que validen paridad y reentrenen, y
  que Héctor regenere `Evaluacion_Modelos.md` de su lado.

## Uso de IA

Sesión completa asistida por Claude (Cowork): diseño de la CTE con `lateral unnest`, las cinco
pruebas dbt, el enum y campo de `contrato.py`, el cálculo espejo en `generar_fixture.py`, y el
diagnóstico de qué pruebas de C3 cambiaban de comportamiento a propósito (para no tocar su reporte
de evaluación) frente a cuáles sí había que ajustar (el test que probaba una rama que dejó de
ocurrir por defecto). Todo el código se corrió y verificó en el ambiente de Claude antes de
entregarlo; revisar línea por línea antes de cada commit, como siempre.
