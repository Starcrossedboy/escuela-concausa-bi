---
project: "FARO"
date: "2026-08-28"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "1h"
touches: ["BUG-018", "US-302", "REQ-003"]
tags: [devlog, celula-3, ml02, cobertura, bugfix]
---

# DevLog — 2026-08-28 — BUG-018 cobertura por ventana en ML-02

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se confirmó la reproducción documentada por Héctor Morales para BUG-018.
- ML-02 ahora calcula drivers utilizables dentro de cada ventana de entrenamiento.
- Los drivers completamente vacíos se excluyen y quedan registrados por ventana.
- La predicción y SHAP usan `modelo.feature_names_in_` para evitar desajustes de forma.
- Se agregó un error accionable cuando ninguna feature tiene datos.
- Se actualizó la documentación porque Gold ya publica `driver_dominante` con prueba de paridad.

## Sesión de IA

- **Agente / modelo:** GitHub Copilot.
- **Archivos creados/modificados:** entrenamiento y pruebas de ML-02, documentación, plan, matriz,
  índice y este DevLog.
- **Decisiones autónomas del agente:** replicar el patrón probado de ML-01 por ventana y no modificar
  el registro global de bugs, que QA/PM debe cerrar después del merge.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** revisar el hallazgo urgente de Héctor y aplicar el arreglo si era correcto.

## Seguridad / calidad

- [x] Sin secretos ni datos reales versionados.
- [x] Regresión específica de BUG-018 aprobada: 2 pruebas.
- [x] Suite de ML-02: 16 pruebas aprobadas.
- [x] Entrenamiento, evaluación y publicación Gold: 68 pruebas aprobadas.
- [x] Suite completa: 454 pruebas aprobadas, 51 omitidas y 1 warning conocido.
- [x] Ruff limpio en implementación y pruebas.
- [x] DevLog enlaza BUG-018, US-302 y REQ-003.

## Bloqueantes

- Falta ejecutar ML-02 contra el Gold real de Diana en un entorno con Postgres y dependencias ML.
- El endpoint SHAP real continúa bajo responsabilidad de Célula 4.

## Próximos pasos

- Solicitar revisión a Héctor por paridad con BUG-015 y a Diana para reanudar el E2E.
- Pedir a QA/PM cerrar BUG-018 cuando el PR sea fusionado.