---
project: "FARO"
date: "2026-08-30"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
touches: ["BUG-025", "US-304a", "US-305", "REQ-006"]
tags: [devlog, agente, llm, anthropic, text-to-sql]
---

# DevLog — 2026-08-30 — BUG-025: adaptador LLM Anthropic

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/06_Quality_Testing/Bug_Register|Bug Register · BUG-025]]

## Objetivo

Implementar la parte C3 de BUG-025 después de cerrar BLOCK-003: generación Text-to-SQL y redacción
de respuestas mediante Anthropic, sin manejar secretos ni modificar los providers de C4.

## Cambios

- Se creó `src/agente/llm.py` con `generar_sql_con_llm()` y
  `redactar_respuesta_con_llm()`.
- Ambas etapas usan salida JSON estructurada, una sola llamada y errores públicos genéricos.
- El cliente real toma `ANTHROPIC_API_KEY` del entorno, usa `AGENTE_MODELO`,
  `AGENTE_MAX_TOKENS` y `AGENTE_TIMEOUT_S`, y desactiva reintentos.
- Se añadió `anthropic>=0.116` a `requirements/celula-3.txt`.
- Se agregaron pruebas offline con cliente inyectable; no requieren API key ni acceso de red.

## Validación

- `.venv\\Scripts\\python.exe -m ruff check src\\agente\\llm.py tests\\test_agente_llm.py` — verde.
- Suite enfocada C3 — **46 passed**.
- La colección del endpoint API no se ejecutó porque el ambiente local no tiene el paquete
  transitivo `limits`; no es causado por este cambio.

## Pendientes externos

- C4 conecta los providers reales sin usar `app.dependency_overrides` en producción.
- C5 instala el requirements de C3 en la imagen y configura Secret Manager/variables.
- PM actualiza BUG-025 y la matriz de trazabilidad cuando se integren las tres partes.
