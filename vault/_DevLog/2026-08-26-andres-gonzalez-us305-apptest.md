---
project: "FARO"
date: "2026-08-26"
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "30m"
touches: ["US-305", "REQ-006"]
tags: [devlog, celula-3, streamlit, testing, agente]
---

# DevLog — 2026-08-26 — AppTest persistente para US-305

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

- Se agregó `tests/test_frontend_chat_streamlit.py` para reemplazar el smoke manual del widget por
  una prueba reproducible.
- La prueba levanta un servidor HTTP efímero, ejecuta dos turnos con `AppTest` y verifica historial,
  SQL auditable y rechazo visible de una operación fuera de alcance.
- El caso usa `pytest.importorskip("streamlit")` para no romper el CI base mientras Streamlit no esté
  declarado en los requirements compartidos.

## Sesión de IA

- **Agente / modelo:** GitHub Copilot.
- **Archivos creados/modificados:** prueba Streamlit, documento US-305, plan individual, matriz de
  trazabilidad, índice y este DevLog.
- **Decisiones autónomas del agente:** usar un servidor HTTP local determinista en vez de Docker o
  una API externa.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** avanzar pendientes propios de Andrés.

## Seguridad / calidad

- [x] Sin secretos, datos reales ni servicios externos.
- [x] Prueba enfocada: 1 passed.
- [x] Suite completa local con Streamlit instalado: 352 passed, 1 warning conocido.
- [x] Ruff limpio.
- [x] DevLog enlaza US-305 y REQ-006.

## Bloqueantes

- El cierre funcional todavía depende de US-304b (RAG de Carlos) y del JWT/API de Célula 4.

## Próximos pasos

- Ejecutar E2E contra la API integrada cuando estén disponibles RAG y autenticación.