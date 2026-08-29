---
project: "FARO"
date: "2026-08-29"
author_human: "Estefany Lucero Hernández Loredo"
agent: "Codex"
model: "GPT-5.6"
session_duration: "~2h"
touches: ["US-321", "REQ-003"]
tags: [devlog, celula-3, ml-03, clustering, kmeans]
---

# DevLog — 2026-08-29 — ML-03 temporal y perfiles

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se implementó KMeans con escalado, selección temporal de `k` por Silhouette y perfiles de
  negocio por cluster.
- Se agregó un guardrail que sólo permite casos completos: no se inventó la imputación pendiente.
- Se preparó el registro del pipeline y métricas en MLflow sin promover un modelo provisional.
- Se añadieron pruebas sintéticas de fuga temporal, ausencia, selección de `k`, perfiles y
  exclusión del target.

## Seguridad / calidad

- [x] `pytest tests/test_entrenar_ml03.py -q`: 6 passed.
- [x] `pytest tests/ -q`: 533 passed, 5 skipped.
- [x] Ruff limpio en módulo y pruebas.
- [x] `vault_lint.py`: Vault limpio.
- [x] Fixtures 100% sintéticos; sin datos reales, credenciales ni archivos pesados.

## Decisión de PR

US-321 se separa del PR de US-322/US-325. El diagnóstico puede aprobarse aunque cambie la política
de entrenamiento; el modelo conserva su propio diff, sus riesgos y su compuerta técnica.

## Pendientes

- Ratificar el fallback de imputación y reentrenar.
- Ejecutar con cuatro ciclos Bronze / tres ciclos efectivos en Gold (BUG-026).
- Registrar la corrida final en MLflow y actualizar la ficha de modelo, cuyo dueño es Carlos.

## Uso de IA

Codex generó la implementación, pruebas y documentación. Estefany debe revisar el código línea por
línea antes del merge.
