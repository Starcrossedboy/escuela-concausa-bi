---
project: "FARO"
date: "2026-09-02"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1 sesión — cierre e2e de OAuth (US-402), state CSRF y revisión de seguridad de US-403/US-404"
touches: ["US-402", "US-403", "US-404", "US-405", "REQ-004", "SEC-002", "SEC-003", "SEC-004", "SEC-005", "SEC-006"]
tags: [devlog, celula-4, api, seguridad, oauth2, jwt, csrf, rbac]
---

# DevLog — 2026-09-02 — Cierre e2e de OAuth con Google, `state` CSRF y revisión de seguridad

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/07_Security/Security_Review_US402_US403_US404]] ·
[[vault/03_Architecture/API_Specification|API_Spec §2.1.1]]

## Contexto

Se abrió la sesión para arrancar **US-405** (login/logout y vistas por rol en FARO Web) y cerrar
**US-403** y **US-404**. La revisión del estado real cambió el plan por dos hallazgos:

1. **US-405 no podía arrancar de verdad.** `RealGoogleVerifier.verify()` seguía levantando
   `NotImplementedError`, así que el login e2e no funcionaba **aunque C5 ya tuviera las credenciales
   vivas en Cloud Run** desde el 30-ago (revisión `faro-api-00007-4dd`). Un frontend contra un login
   que no autentica no es US-405, es andamiaje.
2. **`src/frontend/**` es 🟡 y su dueño es Manuel Serranía (C2)**, además de estar en `criticos:` de
   `ownership.yml`. Se decidió **no tocarlo** en este PR y coordinarlo con él antes.

Así que esta sesión cierra el prerrequisito duro de US-405 —que es 🟢 mío— y deja US-403/US-404
formalmente cerradas con la revisión humana que exige la regla 7.

## Qué se hizo

### 1. `state` anti-CSRF real (`SEC-002`)

`/auth/login` mandaba a Google el literal `state=faro`. Es observable desde fuera, sin credenciales,
en la URL pública, y **no protege de nada**: cualquiera podía reproducirlo y forjar una llamada al
callback con un `code` propio (login CSRF).

Ahora el `state` es un JWT propio de 10 min con `nonce` aleatorio (`create_state_token`), que viaja
por dos canales independientes: el parámetro de la URL de Google y la cookie de primera parte
`faro_oauth_state` (`HttpOnly`, `Secure` fuera de local, `SameSite=Lax`). El callback exige que
ambos existan y coincidan (`secrets.compare_digest`), que el token sea válido y vigente, y consume
la cookie (un solo uso). Cualquier fallo → **401** uniforme, sin decir cuál de las tres condiciones
falló.

**Decisión:** `state` **firmado**, no guardado en memoria del servidor. Cloud Run corre varias
instancias sin estado compartido: un `state` en RAM se perdería entre la ida y la vuelta del
navegador.

### 2. `RealGoogleVerifier` implementado (cierra US-402 e2e)

*Authorization code flow* completo: canje del `code` en el token endpoint y **verificación del
`id_token`** — firma RS256 contra la llave del JWKS público de Google que corresponde al `kid`,
`aud == GOOGLE_CLIENT_ID`, `iss` de Google, `exp` vigente y `email_verified == true` (el rol se
resuelve por correo, así que un correo sin verificar permitiría suplantar a un futuro `analista`).
La lista de algoritmos se pasa explícita: nunca se confía en el `alg` del token entrante. El JWKS se
cachea 1 h y se refresca ante un `kid` desconocido. El módulo no registra ni devuelve el `code`, el
`client_secret` ni el `id_token`.

### 3. Cierre documental de US-403 y US-404

[[vault/07_Security/Security_Review_US402_US403_US404]]: revisión humana explícita (regla 7) con el
checklist ejecutado, la evidencia de pruebas y **cinco hallazgos registrados** en el Security Audit
Log — `SEC-002` resuelto, y `SEC-003`…`SEC-006` aceptados con dueño y condición de cierre
(rate limiting en memoria, HS256, refresh sin rotación, `AUTH_LECTURA_PUBLICA=true`).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5.
- **Creados:** `tests/test_oauth_google.py` (18 casos),
  `vault/07_Security/Security_Review_US402_US403_US404.md`, este DevLog.
- **Modificados:** `src/api/security/google.py` (verifier real + caché JWKS),
  `src/api/security/jwt.py` (`create_state_token`/`verify_state_token`), `src/api/v1/auth.py`
  (cookie y validación del `state`), `src/api/config.py` (endpoints OIDC, emisores, timeouts,
  vida del `state`, `cookies_seguras`), `tests/test_auth_jwt.py` (el callback ahora ejercita
  `login → callback`), `api/openapi.v1.json`, `vault/03_Architecture/API_Specification.md` (§2.1.1),
  `vault/07_Security/Security_Audit_Log.md`, `vault/07_Security/Security_Review_Checklist.md`,
  `vault/07_Security/_index.md`, `vault/_DevLog/_index.md`,
  `vault/02_Requirements/Traceability_Matrix.md`.
- **Revisión manual:** revisado línea por línea. Foco en tres cosas: que ningún 4xx/5xx del flujo
  filtre detalle del intercambio con Google, que la comparación del `state` sea en tiempo constante,
  y que el `id_token` no se acepte por el `alg` que él mismo declara.
- **Cambio de contrato consciente:** un `GET /auth/callback` sin `state` válido ahora devuelve **401**,
  no 200. Documentado en el contrato y reflejado en `openapi.v1.json`.

## Seguridad / calidad

- [x] Sin secretos hardcodeados (todo por `Settings`; el `client_secret` sigue en Secret Manager)
- [x] Pruebas nuevas: `tests/test_oauth_google.py` (18) + `tests/test_auth_jwt.py` actualizado
- [x] `pytest tests/test_oauth_google.py tests/test_auth_jwt.py tests/test_rbac.py tests/test_hardening.py tests/test_api_contract.py -q` → **79 passed**
- [x] `ruff check src/api tests` → limpio
- [x] Revisión humana explícita de seguridad registrada (regla 7)
- [ ] **Suite completa NO ejecutada en local**: esta máquina no tiene el ambiente 3.11 con las
      dependencias de C1/C3 (Great Expectations, MLflow). Lo verifica el CI.
- [ ] **Login e2e contra el Google real no ejecutado por el agente**: requiere meter credenciales
      personales en la pantalla de consentimiento. Lo hace Christian a mano (§Próximos pasos).

## Bloqueantes / avisos a otros owners

- **Manuel Serranía (C2) — `src/frontend/**`:** US-405 depende de este flujo. No se tocó nada de su
  área; hay que acordar quién escribe `auth.py` del frontend y cómo se guardan los tokens.
- **Luis Téllez (C5):** dar de alta a los evaluadores como *test users* de la pantalla de
  consentimiento (sigue en modo Testing) y, tras validar el login en vivo, coordinar el flip de
  `AUTH_LECTURA_PUBLICA=false`. Pendiente también `SEC-003` (rate limiting multi-instancia).
- **Edgar (PO) — dos huecos de `ownership.yml`:** `vault/03_Architecture/ADRs/**` y `.env.example`
  **no tienen dueño**, así que el gate de propiedad reprueba a cualquiera que los toque. Por eso
  `ADR-004` **no** se actualizó en este PR pese a que le corresponden los cambios de §2, y las
  variables nuevas (que tienen default seguro) no se documentaron en `.env.example`.
- **Edgar (PO):** sigue pendiente ratificar `ANALISTA_EMAILS`. Hoy vacío ⇒ todos `ciudadano`.
- **C2 / C3:** `api/openapi.v1.json` se regeneró y arrastró deriva previa que ya estaba en `main` sin
  regenerar (`MunicipioOut.poblacion` pasa a opcional, cotas de `variacion_matricula`, descripción
  del endpoint del agente). El contrato ahora refleja el código; conviene revisar los mocks.
- **Regla 7:** cambio de seguridad → requiere revisión humana explícita en el PR.

## Próximos pasos

1. **Christian, a mano:** validar el login e2e en la URL pública (`/api/v1/auth/login` → consentimiento
   → callback → `TokenPair`) tras el deploy de este cambio, y comprobar `/auth/me` con el token real.
2. **US-405** con Manuel: login/logout y guardas por rol en FARO Web.
3. Follow-ups aceptados: RS256 (`SEC-004`) y rotación/revocación de refresh (`SEC-005`).
