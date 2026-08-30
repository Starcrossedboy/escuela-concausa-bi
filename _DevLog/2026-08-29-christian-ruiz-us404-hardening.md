---
project: "FARO"
date: "2026-08-29"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — hardening de la API (US-404)"
touches: ["US-404", "REQ-004", "ADR-004"]
tags: [devlog, celula-4, api, seguridad, hardening, cors, rate-limit]
---

# DevLog — 2026-08-29 — US-404: Hardening de la API

→ [[_DevLog/_index|Volver al índice]] · [[03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt|ADR-004 §Hardening]] · [[03_Architecture/API_Specification|API_Spec §5]]

## Contexto

Con US-403 (RBAC) ya en `main` (PR #97), se desbloquea US-404: endurecer la superficie HTTP de la
API. Alcance del sprint: **rate limiting, CORS, validación estricta con Pydantic y errores sin fuga
de información interna**. Cae bajo la regla 7 del vault (cambio de seguridad).

## Qué se hizo

- **Rate limiting** por `(IP, path)` configurable (`RATE_LIMIT_DEFAULT`, default `120/minute`).
  Devuelve el `ErrorOut` 429 uniforme. **Decisión técnica:** se eligió `slowapi`, pero su
  `SlowAPIMiddleware` **eximía todo** porque su resolución de ruta no reconoce los routers incluidos
  de esta versión de FastAPI (`_IncludedRouter`). Se usó su **motor `limits`** (misma dependencia) en
  un middleware propio — sin route-resolution frágil y con formato de error del contrato.
- **CORS** con orígenes configurables (`CORS_ORIGINS`, CSV; default = frontends locales). C5 añade los
  de despliegue. Métodos/headers acotados.
- **Validación estricta**: base `EntradaEstricta` (`extra="forbid"`) para los 4 modelos de entrada
  (`RefreshIn`, `PrediccionBatchIn`, `AgenteConsultaIn`, `PipelineRunIn`) → campo desconocido = 422.
  Se refleja como `additionalProperties: false` en el OpenAPI (regenerado).
- **Errores sin fuga**: el handler 500 ahora registra el detalle real en logs (`faro.api`) y devuelve
  mensaje genérico; se mantiene el `ErrorOut` uniforme para todo 4xx/5xx.
- **Pruebas**: `tests/test_hardening.py` (7 casos: CORS simple/preflight, 429 con ErrorOut, límite
  desactivado, 422 por campo extra, body válido, 500 sin fuga). Suite total 622 passed / 5 skipped
  (solo fallan 3 módulos GE de C1 por versión de Great Expectations, ajenos).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos creados:** `tests/test_hardening.py`, este DevLog.
- **Modificados:** `src/api/app.py` (rate limit + CORS + logging), `src/api/config.py` (settings),
  `src/api/schemas.py` (EntradaEstricta), `requirements.txt` (+slowapi), `.env.example`,
  `api/openapi.v1.json`, `03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt.md`, `_DevLog/_index.md`.
- **Decisiones (con el PO/Christian):** (1) rate limiting con `slowapi` sobre solo los 4 items del
  sprint (RS256/rotación de refresh se documentan como follow-up, no se implementan — evita depender
  de llaves de C5). (2) Ante la incompatibilidad de `SlowAPIMiddleware`, usar su motor `limits` en
  middleware propio en vez de decorar rutas de otras células.
- **Revisión manual:** verificado que el 429/500 no filtran configuración ni trazas; ruff limpio.

## Seguridad / calidad
- [x] 429/CORS/validación/500 cubiertos por pruebas (`tests/test_hardening.py`, 7)
- [x] Ningún 4xx/5xx expone trazas, SQL ni configuración interna
- [x] Sin secretos en código; settings por entorno
- [x] DevLog enlaza a los IDs afectados (US-404, REQ-004, ADR-004)

## Bloqueantes / avisos a otros owners
- **C2 (Superset) / C3 (Agente):** los bodies ahora rechazan campos desconocidos (422). Alinear
  mocks/clientes para no enviar extras. Contrato actualizado en `openapi.v1.json`.
- **C5 (Luis):** poblar `CORS_ORIGINS` con la URL real del frontend/deploy; el rate limiting es en
  memoria por proceso → si hay varias instancias en Cloud Run, migrar a Redis (follow-up ADR-004).
- **Follow-up (US-404+):** RS256 (llaves de C5) y rotación/revocación de refresh — documentados en
  ADR-004, no en este PR.
- **Regla 7:** cambio de seguridad → revisión humana explícita.
