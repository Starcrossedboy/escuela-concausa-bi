---
project: "FARO"
date: "2026-08-17"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — núcleo OAuth2/JWT (US-402)"
touches: ["US-402", "REQ-004", "ADR-004", "DOC-SECMODEL"]
tags: [devlog, celula-4, api, seguridad, oauth2, jwt]
---

# DevLog — 2026-08-17 — US-402: núcleo OAuth2 + JWT (access/refresh)

→ [[_DevLog/_index|Volver al índice]] · [[03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt|ADR-004]] · [[03_Architecture/API_Specification|API_Spec §2]]

## Contexto

Con US-401 ya en `main` (PR #19), se desbloquea US-402. Se adelanta el **núcleo de autenticación**
—la maquinaria JWT propia, que es independiente de Google— de forma **offline, sin secretos reales**.
Cae bajo la regla 7 del vault (revisión humana de seguridad).

## Qué se hizo

- **Config tipada** (`src/api/config.py`, pydantic-settings): secret, algoritmo, expiraciones,
  credenciales Google y allowlist de rol. Con **guarda de arranque**: la app se niega a iniciar en
  `production` con secreto inseguro (<32 chars o el default de dev).
- **Núcleo JWT** (`src/api/security/jwt.py`): emisión/validación de access (15 min) y refresh (7 d)
  con claim `type` para no cruzarlos. **Endurecido contra confusión de algoritmo**: `decode` con
  lista explícita de algoritmos, nunca el `alg` del token.
- **`get_current_user`** (`src/api/security/deps.py`): valida el Bearer y devuelve el usuario o **401
  uniforme** (`ErrorOut`), sin filtrar la causa.
- **Flujo Google desacoplado** (`src/api/security/google.py`): URL de consentimiento + interfaz
  `GoogleVerifier`; la verificación real queda pendiente de credenciales (Célula 5) y se prueba con
  un verificador falso.
- **Política de rol provisional** (`src/api/security/roles.py`): mínimo privilegio (todos ciudadano
  salvo allowlist `ANALISTA_EMAILS`). La definitiva la decide Edgar/PO.
- **Endpoints `/auth/*` reales**: login→Google, callback→emite par, refresh→re-resuelve rol, me→protegido.
- **ADR-004** (decisiones + riesgos + plan RS256) y vars de auth repuestas en `.env.example`.
- **15 pruebas nuevas** (`tests/test_auth_jwt.py`) + ajuste del test de `/auth/me` en US-401.
  Suite completa: **157 passed, 4 skipped** con `requirements.txt` (paridad con CI).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos creados:** `src/api/config.py`, `src/api/security/{__init__,jwt,google,roles,deps}.py`,
  `03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt.md`, `tests/test_auth_jwt.py`.
- **Modificados:** `src/api/v1/auth.py`, `src/api/app.py` (lifespan + guarda prod),
  `.env.example`, `requirements.txt` (+python-jose), `api/openapi.v1.json`, `tests/test_api_contract.py`,
  `03_Architecture/ADRs/_index.md`.
- **Decisiones autónomas:** HS256 con migración documentada a RS256; `decode` con algoritmos
  explícitos (mitiga CVE de python-jose); rol re-resuelto en cada refresh; mínimo privilegio por
  defecto; guarda anti-secreto-débil en producción; `lifespan` en vez de `on_event`.
- **Revisión manual:** revisado línea por línea; foco en no filtrar secretos ni detalles internos.

## Seguridad / calidad
- [x] Sin secretos hardcodeados (solo placeholders; default de dev claramente marcado inseguro)
- [x] Tests agregados (`tests/test_auth_jwt.py`, 15 casos; suite 157 passed / 4 skipped)
- [x] DevLog enlaza a los IDs afectados (US-402, REQ-004, ADR-004, DOC-SECMODEL)

## Bloqueantes / avisos a otros owners
- **Célula 5 (Luis):** provisionar `GOOGLE_CLIENT_ID/SECRET` + `redirect_uri` y el secreto JWT en
  Secret Manager. Reponer/validar las vars de auth que añadí a `.env.example` (C5 reestructuró ese archivo).
- **Edgar/PO:** definir la **política de rol** definitiva (quién es `analista`). Hoy: allowlist vacía.
- **Edgar (owner de `07_Security/Security_Model.md`):** actualizar la sección Autenticación (hoy es
  placeholder) para reflejar OAuth2+JWT de ADR-004. No lo edité por no ser artefacto propio.
- **Regla 7:** este PR es cambio de seguridad → requiere revisión humana explícita.

## Próximos pasos
- US-403 (RBAC): `require_role(...)` sobre `get_current_user`, y proteger endpoints de datos/admin.
- Cerrar el flujo Google e2e cuando lleguen credenciales; `state` CSRF y almacenamiento de tokens en US-405.
- US-404 (hardening): evaluar PyJWT/RS256, rate limiting, rotación/revocación de refresh.
