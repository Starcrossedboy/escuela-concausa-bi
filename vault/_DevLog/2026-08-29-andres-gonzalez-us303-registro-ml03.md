---
project: "FARO"
date: "2026-08-29"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "45m"
touches: ["US-303", "US-321", "REQ-003", "AC-003.4"]
tags: [devlog, celula-3, mlflow, registry, ml03]
---

# DevLog — 2026-08-29 — Registro canónico de ML-03

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se integró ML-03 con el helper compartido `registrar_sklearn` de Célula 3.
- El entrenamiento crea una versión con el nombre canónico `ML03_ClusteringEscuelas`.
- Se conservaron los parámetros de clustering y las métricas de Silhouette y cobertura.
- Se agregó una prueba que exige `registrar_modelo=True`, el nombre canónico y la métrica temporal.

## Decisión técnica

Crear una versión en Model Registry no equivale a promover el modelo a producción. La política de
casos completos sigue siendo provisional y la ficha prohíbe promover o interpretar el artefacto
como productivo hasta que se ratifique la política final.

## Seguridad y calidad

- [x] Sin secretos, credenciales ni datos reales.
- [x] Suite enfocada de ML-03: 7 pruebas aprobadas.
- [x] Cambio limitado a `src/modelos/**`, pruebas y trazabilidad de REQ-003.

## Bloqueantes

- La rama depende del PR de `US-321` de Estefany.
- Falta ejecutar el registro contra MLflow real y verificar conjuntamente ML-01, ML-02 y ML-03.
- La exposición vía API permanece a cargo de Célula 4.

## Próximo paso

- Abrir un PR apilado contra `feat/estefany-loredo-us321-clustering`; después del merge de US-321,
  cambiar la base a `main` y ejecutar el E2E del Registry.
