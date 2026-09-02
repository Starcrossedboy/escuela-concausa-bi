---
project: "FARO"
date: "2026-08-28"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "1h"
touches: ["US-304a", "US-304b", "US-305", "US-323", "REQ-006"]
tags: [devlog, celula-3, rag, chromadb, evaluacion, guardrails]
---

# DevLog — 2026-08-28 — Integración RAG y evaluación del agente

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

- La recuperación carga embeddings de forma diferida y permite inyectar cliente/modelo sin red.
- Los fallos de RAG son errores tipados y ya no se incorporan al prompt como contexto válido.
- El indexador usa IDs deterministas, reporta total indexado y falla visiblemente ante errores.
- El catálogo RAG incluye `driver_dominante` y su carácter de etiqueta operativa derivada.
- `procesar_consulta_con_rag()` conecta recuperación real con los guardarraíles.
- Las 20 preguntas de US-323 recorren el flujo simulado y garantizan cero ejecuciones inseguras.

## Sesión de IA

- **Agente / modelo:** GitHub Copilot.
- **Archivos creados/modificados:** recuperación, indexación, servicio y pruebas del agente;
  documentación, plan, matriz, índice y este DevLog.
- **Decisiones autónomas del agente:** mantener LLM, ejecución SQL y API como dependencias inyectables
  para no invadir Célula 4; representar indisponibilidad RAG como fallo operativo, no fuera de alcance.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** avanzar RAG y evaluación mientras BUG-018 espera merge.

## Seguridad / calidad

- [x] Sin secretos, datos reales ni descargas en pruebas.
- [x] SQL inseguro nunca alcanza el ejecutor.
- [x] 32 pruebas enfocadas aprobadas.
- [x] Suite completa: 460 aprobadas, 51 omitidas y 1 warning conocido.
- [x] Ruff limpio.
- [x] DevLog enlaza los IDs afectados.

## Bloqueantes

- Célula 4 debe conectar el servicio al endpoint real del agente.
- US-405 debe completar el login frontend.
- Falta E2E con ChromaDB, embeddings, Gold y API levantados.

## Próximos pasos

- Ejecutar indexación y consulta real en Docker cuando estén disponibles los servicios.
- Conectar el widget al endpoint integrado y validar JWT/RBAC.