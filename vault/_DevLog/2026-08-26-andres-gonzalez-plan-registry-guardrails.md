---
project: "FARO"
date: "2026-08-26"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "1h"
touches: ["US-302", "US-303", "US-304a", "US-305", "REQ-003", "REQ-006"]
tags: [devlog, celula-3, mlflow, guardrails, plan]
---

# DevLog — 2026-08-26 — Plan, Registry y guardarraíles

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se actualizó el plan individual con el estado real de US-301, US-302, US-303, US-304a y US-305.
- Se instaló Python 3.11.9 en un entorno aislado; la suite completa cerró con 351 pruebas en verde
  después de rebasar la rama sobre `origin/main`.
- Se entrenó ML-02 y se verificó su registro local en MLflow 3.15.1 como
  `ML02_DriverClasificador` versión 1.
- Se confirmó que el contrato del agente comunica la razón de rechazo en `respuesta` y usa
  `fuera_de_alcance=true` como indicador estructurado.
- Se activó el widget Streamlit de US-305 con cliente HTTP desacoplado, historial de sesión,
  manejo de rechazo y visualización auditable del SQL generado.

## Sesión de IA

- **Agente / modelo:** GitHub Copilot.
- **Archivos creados/modificados:** plan individual, documentación de ML-02, guardarraíles, widget
  de chat, cliente HTTP, índice de modelos, matriz de trazabilidad y DevLog.
- **Decisiones autónomas del agente:** porcentajes conservadores basados en evidencia ejecutable y
  separación explícita entre Registry local validado y servidor Docker pendiente.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** avanzar las actividades asignadas e instalar lo necesario.

## Archivos del diff

- **Creados:** `src/frontend/agente_client.py`, `tests/test_frontend_agente_client.py`,
  `vault/15_ML_Models/Widget_Chat_US305.md` y este DevLog.
- **Modificados:** `src/frontend/pages/3_Chat.py`, el plan individual, la matriz de trazabilidad,
  documentos e índice de `vault/15_ML_Models`, y `vault/_DevLog/_index.md`.

## Seguridad / calidad

- [x] Sin secretos hardcodeados.
- [x] 71 pruebas enfocadas aprobadas con Python 3.11.9.
- [x] Registry local de ML-02 validado con backend temporal; no se persistieron datos ni credenciales.
- [x] Cliente del agente cubierto por pruebas con transporte falso; página cargada con `AppTest`;
  Ruff limpio.
- [x] DevLog enlaza a los IDs afectados.

## Bloqueantes

- Falta repetir el registro contra el servidor MLflow de Docker; este checkout no tiene `.env`.
- US-303 necesita ML-03 de Estefany y la integración de inferencia de Célula 4.
- US-304a necesita la capa RAG de Carlos y el set de evaluación de US-323.
- El PM debe reconciliar `Execution_Status.md` tras revisar este avance; no se modificó esa fuente
  canónica desde una rama de contribuidor.

## Próximos pasos

- Coordinar el arranque de US-321 con Estefany.
- Configurar el entorno local de Compose sin versionar secretos y validar el Registry compartido.
- Integrar guardarraíles con US-304b durante Sprint 5.