---
project: "FARO"
date: "2026-08-28"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "1h"
touches: ["BUG-024", "US-304a", "US-305", "REQ-006"]
tags: [devlog, celula-3, seguridad, guardrails, rag]
---

# DevLog — 2026-08-28 — BUG-024 y semántica de recuperación RAG

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se bloqueó `SELECT INTO`, escritura de PostgreSQL que atravesaba el filtro de solo lectura.
- Se agregó una regresión directa para el ataque reportado por Edgar.
- Se separó `ContextoNoEncontrado` de una indisponibilidad operativa de ChromaDB.
- El usuario recibe un mensaje específico cuando no hay coincidencias y otro cuando RAG está caído.
- Se auditó la suite con `-rs`: faltaban PyYAML y Streamlit en `.venv`.
- Se sincronizó el entorno y se declaró Streamlit en requisitos de Célula 3.

## Sesión de IA

- **Agente / modelo:** GitHub Copilot.
- **Archivos creados/modificados:** guardarraíles, recuperación, servicio, pruebas, registro de bugs,
  documentación, requirements, matriz, índice y este DevLog.
- **Decisiones autónomas del agente:** representar cero coincidencias con una excepción específica;
  mantener ocultos los detalles internos de errores operativos.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** atender las observaciones posteriores al merge del PR #119.

## Seguridad / calidad

- [x] BUG-024 tiene prueba de regresión.
- [x] 32 pruebas enfocadas aprobadas.
- [x] Suite completa local: 526 aprobadas, 0 omitidas y 1 warning conocido.
- [x] Ruff limpio.
- [x] Sin secretos, datos reales ni detalles internos expuestos al LLM.

## Bloqueantes

- BUG-025 sigue abierto hasta conectar el servicio real al endpoint de Célula 4.
- Falta el visto bueno de Carlos en el hilo del PR por la evolución del contrato RAG.

## Próximos pasos

- Solicitar revisión técnica de Carlos mediante comentario, no como compuerta adicional.
- Coordinar con Célula 4 la conexión de `procesar_consulta_con_rag()` al endpoint.