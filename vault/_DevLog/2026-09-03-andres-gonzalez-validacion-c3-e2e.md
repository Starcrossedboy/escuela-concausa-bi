---
id: DEVLOG-2026-09-03-ANDRES-GONZALEZ-C3-E2E
project: "FARO"
date: "2026-09-03"
owner: "Andrés González Habib"
status: filed
author_human: "Andrés González Habib"
agent: "GitHub Copilot"
model: "GitHub Copilot"
session_duration: "1h"
touches: ["US-302", "US-303", "US-304a", "US-305", "REQ-003", "REQ-006"]
traces_up: ["REQ-003", "REQ-006"]
traces_down: ["US-302", "US-303", "US-304a", "US-305"]
tags: [devlog, celula-3, validacion, rag, mlflow, oauth]
---

# DevLog — 2026-09-03 — Validación C3 y preparación de E2E

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo
- Se sincronizó `dev/andres-gonzalez` con `origin/main` y se confirmaron integrados US-304b, US-405 y el fix de MLflow para BUG-041.
- Se revisó el contrato del agente: `AgenteConsultaIn` recibe únicamente `pregunta` y rechaza campos extra; el cliente del chat ya cumple ese contrato.
- Se verificó la integración de OAuth en el frontend: `auth.py` guarda el token de acceso en sesión y el widget de US-305 lo propaga como Bearer a la API.
- Los diagnósticos estáticos de `src/agente/**` y `src/modelos/**` no reportaron errores.
- Se agregó `src/agente/verificar_e2e.py`: sonda autenticada que exige `FARO_API_BASE_URL` y `FARO_ACCESS_TOKEN`, verifica una lectura RAG y confirma el rechazo de una instrucción destructiva sin imprimir secretos.
- Se agregaron tres pruebas offline para la sonda: precondiciones, camino de lectura con rechazo de escritura y degradación si el RAG/LLM no genera SQL.

## 🤖 Sesión de IA
- **Agente / modelo:** GitHub Copilot
- **Archivos creados/modificados:** `src/agente/verificar_e2e.py`, `tests/test_verificar_e2e_agente.py`, `vault/_DevLog/2026-09-03-andres-gonzalez-validacion-c3-e2e.md`, `vault/_DevLog/_index.md`, `vault/02_Requirements/Traceability_Matrix.md`
- **Decisiones autónomas del agente:** no modificar `docker/api.Dockerfile` ni `src/frontend/**`, porque pertenecen a C5 y C2 respectivamente.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** "avanza en todo esto que me estas diciendo".

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [ ] Tests agregados/actualizados (no se modificó código)
- [x] DevLog enlaza a los IDs afectados
- Diagnósticos de VS Code: sin errores en `src/agente/**` ni `src/modelos/**`.
- El entorno existente `.venv` usa Python 3.12; se creó `.venv311` para validar con Python 3.11. El terminal no devolvió resumen de `pytest`, por lo que no se declara una suite verde sin evidencia observable.
- La sonda comprobó que falla de forma explícita y segura cuando faltan las variables obligatorias, sin hacer llamadas de red.
- `python -m unittest discover -s tests -p test_verificar_e2e_agente.py -v`: 3 pruebas en verde con Python 3.11.
- Ruff sobre `tests/test_verificar_e2e_agente.py`: limpio tras ajustar el tipo de retorno del context manager y combinar contextos `with`.

## Bloqueantes
- El E2E real de `widget → API → RAG` dentro de Docker/Cloud Run depende de C5: `docker/api.Dockerfile` instala únicamente `requirements.txt`; no incorpora `chromadb` ni `sentence-transformers` de `requirements/celula-3.txt`.
- La validación contra la URL pública además requiere el redeploy de C5 con esa imagen y la configuración disponible del LLM.

## Próximos pasos
- C5 debe incorporar las dependencias de C3 en la imagen API y redesplegar.
- Con la imagen disponible, ejecutar `python -m src.agente.verificar_e2e` con `FARO_API_BASE_URL` y un `FARO_ACCESS_TOKEN` efímero, y registrar el resultado antes del freeze.