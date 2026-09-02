---
project: "FARO"
date: "2026-08-26"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — RBAC de 2 roles (US-403)"
touches: ["US-403", "REQ-004", "ADR-004"]
tags: [devlog, celula-4, api, seguridad, rbac, roles]
---

# DevLog — 2026-08-26 — US-403: RBAC con los 2 roles del PRD

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt|ADR-004 §RBAC]] · [[vault/03_Architecture/API_Specification|API_Spec §3]]

## Contexto

Con US-402 (OAuth2+JWT) ya en `main` (PR #43 mergeado), se desbloquea US-403: **enforcement por
rol**. El PRD define dos roles — `ciudadano` (dashboards + agente) y `analista` (pipelines, export en
bruto, ML avanzado). Cae bajo la regla 7 del vault (revisión humana de seguridad).

## Qué se hizo

- **Dependencias RBAC reutilizables** (`src/api/security/rbac.py`, nuevo), sobre `get_current_user`:
  - `require_role(*roles)` → **403** uniforme (`ErrorOut`) si el rol no está permitido; **401** si no
    hay sesión (lo emite `get_current_user` antes).
  - `require_lectura` → protege la lectura con un **interruptor híbrido** `AUTH_LECTURA_PUBLICA`.
- **Enforcement centralizado** en `src/api/v1/__init__.py` a nivel de `include_router`, **sin tocar**
  los routers de otras células (gold/predicciones son de US-411/US-412). Matriz:
  - `health`, `auth` → públicos.
  - `gold`, `predicciones`, `agente` → `require_lectura`.
  - `admin` → `require_role(analista)` siempre.
- **Flag híbrido** `AUTH_LECTURA_PUBLICA` (default `true`) en `config.py` + `.env.example`: la lectura
  es pública mientras el login Google no esté operativo (credenciales pendientes de C5), para no
  bloquear la URL viva de la demo (rúbrica). Se apaga sin re-tocar código cuando lleguen credenciales.
- **OpenAPI** regenerado: 12 paths ahora declaran `security: bearerAuth` (RBAC visible en el contrato).
- **10 pruebas nuevas** (`tests/test_rbac.py`): matriz 401/403/200 en admin y ambas ramas del flag en
  lectura + unidad de `require_role`. Ajustado `test_admin_pipeline_run_202` (ahora exige analista).
  Suite API completa verde; suite total **358 passed / 5 skipped** con `requirements.txt`.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos creados:** `src/api/security/rbac.py`, `tests/test_rbac.py`, este DevLog.
- **Modificados:** `src/api/config.py` (+flag), `src/api/v1/__init__.py` (wiring RBAC),
  `.env.example`, `api/openapi.v1.json`, `tests/test_api_contract.py`,
  `vault/03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt.md` (§RBAC).
- **Decisión con el PO (Christian):** política de lectura **híbrida con flag** (pública por defecto,
  admin siempre analista). Elegida sobre "lectura pública fija" o "lectura=ciudadano fija" para no
  arriesgar la demo viva ni renunciar al RBAC completo. Enforcement a nivel router (no invadir código
  de otras células). Ambas ramas del flag cubiertas por pruebas.
- **Revisión manual:** revisado línea por línea; foco en que el 401/403 no filtre detalle interno y en
  que el flag nunca relaje el admin.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] El admin (`/admin/*`) exige `analista` de forma incondicional (el flag solo afecta lectura)
- [x] Tests agregados (`tests/test_rbac.py`, 10 casos); suite total 358 passed / 5 skipped
- [x] DevLog enlaza a los IDs afectados (US-403, REQ-004, ADR-004)

## Bloqueantes / avisos a otros owners
- **Célula 5 (Luis):** al entregar credenciales OAuth de Google, poner `AUTH_LECTURA_PUBLICA=false` en
  el entorno de despliegue para exigir sesión `ciudadano` en la lectura.
- **Edgar/PO:** sigue pendiente la **política de rol** definitiva (`ANALISTA_EMAILS`). Hoy allowlist vacía.
- **Célula 1 (Diana):** en mi venv local (pisos de `requirements.txt`, sin pin) fallan por versión de
  Great Expectations `test_validacion_sinaica.py` (import roto) y 4 de `test_validacion_sesnsp.py`.
  Ajenos a este cambio; verificar el pin de GE en CI. No los toqué (no son artefactos propios).
- **Regla 7:** este PR es cambio de seguridad → requiere revisión humana explícita.

## Próximos pasos
- US-404 (hardening): rate limiting, CORS, PyJWT/RS256, rotación/revocación de refresh.
- Cerrar el flujo Google e2e (`state` CSRF) cuando lleguen credenciales; US-405 (frontend login/logout).
