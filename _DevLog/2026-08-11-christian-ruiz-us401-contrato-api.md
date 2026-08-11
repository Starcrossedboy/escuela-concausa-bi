---
project: "FARO"
date: "2026-08-11"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — publicación del contrato de la API (US-401)"
touches: ["US-401", "REQ-004", "DOC-APISPEC"]
tags: [devlog, celula-4, api, contrato, openapi, fastapi]
---

# DevLog — 2026-08-11 — US-401: publicación del contrato de la API (OpenAPI + stub)

→ [[_DevLog/_index|Volver al índice]] · [[03_Architecture/API_Specification|API_Spec]] · [[02_Requirements/Traceability_Matrix|Matriz]]

## Contexto

US-401 (Sprint 1) pedía **definir y publicar el contrato de la API** para desbloquear a las Células 2
y 3. El documento de contrato [[03_Architecture/API_Specification]] ya existía y estaba bien, pero su
§6 promete un artefacto que **faltaba**: el `api/openapi.v1.json` estable del que se levantan los mocks.
Esta sesión convierte el contrato en algo **ejecutable, mockeable y verificado**.

## Qué se hizo

- **Modelos Pydantic del contrato** (`src/api/schemas.py`): 1:1 con el §4 de la API_Spec (Page[T],
  roles, escuelas/municipios/KPIs, predicciones ML-01/02/03, SHAP, agente, admin y `ErrorOut`).
- **Stub de referencia FastAPI** (`src/api/app.py` + `src/api/v1/*`): catálogo completo de endpoints
  del §3 bajo `/api/v1`, con manejadores de error uniformes del §5 (401/403/404/422/429/500 →
  `ErrorOut` con `request_id`, sin fuga de trazas/SQL/rutas).
- **Datos de ejemplo 100 % sintéticos** (`src/api/mock_data.py`): 4 escuelas (una por entidad del
  alcance) y sus municipios, con `SIN_DATO` explícito (None) en drivers sin cobertura y recomendación
  prescriptiva por driver dominante (el diferenciador ML-02).
- **Publicación del artefacto** (`api/openapi.v1.json`) vía `scripts/export_openapi.py` (idempotente).
- **Pruebas de contrato** (`tests/test_api_contract.py`, 18 casos): rutas, códigos, formas `Page`/
  `ErrorOut`, rechazo de escritura por el agente y **sincronía del OpenAPI publicado con el código**.
- **Doc operativo** `api/README.md`: cómo regenerar y cómo levantar el mock (FastAPI o Prism).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos creados:** `src/api/schemas.py`, `src/api/mock_data.py`, `src/api/app.py`,
  `src/api/v1/{__init__,common,health,auth,gold,predicciones,agente,admin}.py`,
  `scripts/export_openapi.py`, `api/openapi.v1.json`, `api/README.md`,
  `tests/test_api_contract.py`, `requirements/celula-4.txt`.
- **Decisiones autónomas del agente:** (1) construir el stub como app **independiente**
  (`src/api/app.py`) sin tocar el entrypoint de deploy `src/api/main.py` de la Célula 5; (2) declarar
  el esquema `bearerAuth` en el OpenAPI pero **no** forzar auth/roles (eso es US-402/403); (3) usar el
  literal `422` en vez del constante deprecado de Starlette.
- **Correcciones manuales / revisión:** revisado línea por línea; las 18 pruebas corren en verde.

## Seguridad / calidad
- [x] Sin secretos hardcodeados (datos 100 % sintéticos; sin `.env` ni credenciales)
- [x] Tests agregados (`tests/test_api_contract.py`, 18 casos en verde)
- [x] DevLog enlaza a los IDs afectados (US-401, REQ-004, DOC-APISPEC)

## Bloqueantes / avisos a otros owners
- **DOC-APISPEC (owner Karla / MOC Edgar):** tras el swap del 2026-08-06, US-401 es de Christian, pero
  el frontmatter sigue con `owner: Karla` y `last_reviewed: 2026-08-03` (previo al swap). **Se propone
  a Edgar** actualizar owner/last_reviewed y pasar el status de `in_review` a `approved` (el contrato ya
  tiene forma ejecutable y pruebas).
- **Célula 5 (Luis, US-501):** cuando US-402 monte `/api/v1` en el servicio desplegado, coordinar el
  cambio de `src/api/main.py` para no romper el Dockerfile/deploy.

## Próximos pasos
- US-402 (OAuth2/JWT con Google) y US-403 (RBAC) rellenan el stub con auth y enforcement reales.
- US-404: rate limiting, CORS y validación estricta sobre esta base.
