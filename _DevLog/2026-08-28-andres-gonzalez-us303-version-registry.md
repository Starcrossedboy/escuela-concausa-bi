---
project: "FARO"
date: "2026-08-28"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "30m"
touches: ["US-303", "REQ-003", "AC-003.4"]
tags: [devlog, celula-3, mlflow, registry]
---

# DevLog — 2026-08-28 — Validación de versiones del Registry

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se fortaleció el verificador de MLflow para convertir las versiones a enteros antes de elegir la más reciente.
- Una versión nula o no numérica ahora produce un error accionable que identifica el modelo afectado.
- Se agregó una prueba de regresión para metadatos de versión inválidos.

## Sesión de IA

- **Agente / modelo:** GitHub Copilot.
- **Archivos modificados:** `src/modelos/mlflow_utils.py`, `tests/test_mlflow_utils.py`, matriz de trazabilidad, índice y este DevLog.
- **Decisiones autónomas del agente:** mantener el cambio limitado al verificador compartido de `US-303`, sin intervenir en la API de Célula 4.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** avanzar una actividad propia y dejar la rama lista para abrir PR.

## Seguridad / calidad

- [x] Sin secretos, credenciales ni datos reales.
- [x] Pruebas enfocadas de Registry: 15 aprobadas.
- [x] Sin errores estáticos en los archivos Python modificados.

## Bloqueantes

- `US-303` no se declara terminada: falta registrar ML-03 y completar la integración final de inferencia con Célula 4.

## Próximo paso

- Abrir PR de esta mejora defensiva y, cuando ML-03 esté disponible, ejecutar la verificación conjunta de los tres modelos.
