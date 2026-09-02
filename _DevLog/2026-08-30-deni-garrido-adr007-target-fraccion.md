---
project: "FARO"
date: "2026-08-30"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
session_duration: "normalización de target Gold conforme ADR-007"
touches: ["ADR-007", "US-112", "US-113", "US-313", "BUG-017"]
tags: [devlog, adr007, gold, features, target, ml]
---

# ADR-007 — target_variacion_matricula en fracción

→ [[_DevLog/_index|Volver al índice]] · [[03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula]]

## Contexto

La validación runtime de US-113 con DS-07 real llegó correctamente hasta
`gold.features_escuela`, pero el job canónico de Célula 3
`python -m src.modelos.publicar_gold --desde-gold` se detuvo porque
`target_variacion_matricula` seguía expresado en alumnos absolutos.

ADR-007 está `accepted` y ratifica que la unidad canónica es fracción del ciclo anterior.

## Cambio

- `gold.features_escuela.target_variacion_matricula` pasa de
  `matricula_total - matricula_ciclo_anterior` a
  `matricula_total / matricula_ciclo_anterior - 1.0`.
- No se usa `NULLIF` sobre matrícula previa: un denominador cero debe bloquear explícitamente.
- Se agregan dos pruebas singulares dbt:
  - paridad exacta del target publicado contra la fórmula ADR-007;
  - rechazo de cualquier observación con `matricula_ciclo_anterior = 0`.
- No se modifica ML, riesgo, predicciones, recomendaciones ni cubos.

## Validaciones

- `dbt run --select features_escuela`: PASS
- tests ADR-007: PASS
- filas features: 145
- target min: -0.25531915
- target mediana: 0.00000000
- target max: 0.38709677
- `verificar_escala_variacion()` sobre Gold real: PASS
- suite `pytest tests/ -q`: PASS
- `vault_lint.py`: PASS
- `git diff --check`: PASS

