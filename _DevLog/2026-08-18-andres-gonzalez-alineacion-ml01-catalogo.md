---
project: "FARO"
date: "2026-08-18"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "1h"
touches: ["US-301", "US-302", "ADR-003", "DOC-ML-STRATEGY", "DOC-ML01-ENTRENAMIENTO", "TEST-007"]
tags: [devlog, celula-3, ml, metricas, recomendaciones]
---

# DevLog — 2026-08-18 — Alineación de ML-01 y catálogo de recomendaciones

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se alinearon los umbrales de ML-01 con `target_variacion_matricula`, cuya unidad es una proporción:
  MAE < 0.03 (3 puntos porcentuales) y RMSE < 0.05 (5 puntos porcentuales).
- Se documentó en ADR-003 por qué no es reproducible convertir el error a alumnos sin una matrícula
  base en el contrato de features.
- Se actualizó el generador reproducible de US-312 y se agregó una prueba contra la regresión al
  umbral anterior `MAE < 15 alumnos`.
- Se creó `src/modelos/recomendaciones.py` como catálogo canónico de Célula 3; ML-02 y la publicación
  Gold ahora lo consumen sin cambiar sus APIs actuales.

## Decisiones

- Los umbrales permanecen provisionales hasta evaluar datos reales de US-104.
- No se modificó `src/api/mock_data.py`, propiedad de Célula 4. La prueba existente de Gold mantiene
  la igualdad de textos; Christian Ruiz debe autorizar que API importe directamente el catálogo
  canónico para eliminar esa última copia.
- No se regeneró manualmente `06_Quality_Testing/Automated/Evaluacion_Modelos.md`: pertenece a Héctor
  y declara que solo debe escribirse mediante `python -m src.modelos.evaluar`.

## Validación

- `python -m pytest tests/test_evaluar.py -vv` — 14 passed.
- `python -m pytest tests/test_entrenar_ml02.py -vv` — 8 passed.
- `python -m pytest tests/test_publicar_gold.py -vv` — 18 passed.
- `python -m ruff check src/modelos/recomendaciones.py src/modelos/entrenar_ml02.py src/modelos/evaluar.py src/modelos/publicar_gold.py tests/test_evaluar.py` — limpio.

## Próximo paso

- Solicitar revisión de Edgar para ADR-003 y de Christian para sustituir la copia del catálogo en API.
- Tras aprobación de Héctor, regenerar el reporte US-312 con los umbrales alineados.
