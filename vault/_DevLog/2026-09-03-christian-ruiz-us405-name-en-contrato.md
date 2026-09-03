---
project: "FARO"
date: "2026-09-03"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1 sesión — `name` en UserOut para US-405 y hallazgo del puente OAuth → Streamlit"
touches: ["US-405", "US-402", "REQ-004", "DOC-APISPEC"]
tags: [devlog, celula-4, api, contrato, oauth2, us405, frontend]
---

# DevLog — 2026-09-03 — `name` en el contrato de sesión (US-405)

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/03_Architecture/API_Specification|API_Spec §7]] ·
[[vault/03_Architecture/Frontend_Architecture]]

## Contexto

Con US-402/403/404 ya en `main` (PR #197) y el shell de FARO Web de Manuel también mergeado,
arranca US-405. Al cruzar el front con el contrato apareció un choque: `app.py:24` leía
`user['name']`, pero `/auth/me` devolvía `{sub, email, role}` — **sin `name`**. No se veía porque
el objeto de sesión era un stub hecho a mano; en cuanto `current_user()` hablara con la API real,
`KeyError`.

Acordado con Manuel (C2) por escrito: yo agrego `name` al contrato, él blinda `app.py` con
`user.get('name') or user['email']` como red de seguridad independiente del orden de merge. Las dos
mitades ya están.

## Qué se hizo

- **`UserOut.name`** (`src/api/schemas.py`), `StrictStr` con default `""`. **Opcional a propósito:**
  no todo perfil de Google expone el claim, y la sesión no debe depender de un dato de presentación.
- **`GoogleIdentity.name`** y extracción del claim `name` del `id_token` (ya pedíamos scope
  `profile`, así que el dato venía y se estaba tirando). Se usa `claims.get("name") or ""` y no
  `get("name", "")`: si Google manda `name: null`, `str(None)` habría metido la cadena `"None"` en
  el token — el caso está cubierto por prueba.
- **`name` viaja en los dos tokens.** En el access token es obvio; en el **refresh** también, porque
  al renovar no hay `id_token` que reconsultar y el nombre se perdería en la primera renovación.
- `/auth/me` lo devuelve vía `get_current_user`.

**Frontera de seguridad, explícita:** `name` es **solo de presentación**. El rol se resuelve por
`email` en `security/roles.py` y nunca por `name` — hay una prueba que lo fija
(`test_name_no_influye_en_el_rol`), porque es justo la clase de campo que alguien podría empezar a
usar para autorizar sin darse cuenta.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5.
- **Modificados:** `src/api/schemas.py`, `src/api/security/google.py`, `src/api/security/jwt.py`,
  `src/api/security/deps.py`, `src/api/v1/auth.py`, `tests/test_oauth_google.py` (+5 casos),
  `api/openapi.v1.json`, `vault/03_Architecture/API_Specification.md`, este DevLog,
  `vault/_DevLog/_index.md`, `vault/02_Requirements/Traceability_Matrix.md`.
- **Revisión manual:** revisado línea por línea. El foco fue que `name` no se cuele en ninguna
  decisión de autorización y que un `name` ausente o nulo no rompa el login.

## Seguridad / calidad

- [x] `pytest tests/test_oauth_google.py tests/test_auth_jwt.py tests/test_rbac.py tests/test_hardening.py tests/test_api_contract.py -q` → **84 passed**
- [x] `ruff check src/api tests` → limpio
- [x] Sin secretos ni datos personales en el repositorio (ver bloqueante de `ANALISTA_EMAILS` abajo)
- [ ] Suite completa: la corre el CI (esta máquina no tiene el ambiente 3.11 de C1/C3)

## Bloqueantes / avisos a otros owners

- **Andrés (C3):** cambio de contrato — `UserOut` gana `name` (opcional, `""` por defecto). Es
  aditivo: nada de lo que ya consumes se rompe.
- **Edgar (PO) — `ANALISTA_EMAILS`:** política definida. Entra **solo Edgar** como `analista`;
  Christian se queda `ciudadano` a propósito, para poder demostrar los **dos** roles en vivo (con
  ambos en la allowlist no habría quien enseñara la vista de rol estándar). **Ningún correo se
  versiona en el repositorio**: son datos personales y el `deploy-cloud-run.sh` lo declara
  explícitamente ("NO se versiona ningún correo"). Se carga efímero por variable de entorno; el
  comando queda en manos de Luis (C5).
- **Luis (C5):** falta el redeploy con el código de US-402 ya mergeado, y cargar `ANALISTA_EMAILS`.
  Hasta entonces no se puede validar el login e2e en la URL pública.

## Hallazgo abierto — el puente OAuth → Streamlit no está diseñado

`Frontend_Architecture.md` §3 dice que el front "redirige al `/auth/login` de la API y guarda el
access/refresh token en `st.session_state`", pero **no dice cómo llega el token de vuelta al
front**. Hoy el flujo termina en `/auth/callback`, que responde el `TokenPair` como **JSON en el
navegador**: la persona ve un blob de JSON en la pantalla y Streamlit nunca se entera.

No es un bug de lo implementado — el flujo de la API es correcto y está probado. Es una pieza de
diseño que falta y que **bloquea US-405**. Requiere decisión antes de escribir `src/frontend/auth.py`;
las opciones y su costo quedan para la siguiente sesión.

## Próximos pasos

1. Decidir el puente OAuth → Streamlit (arriba) y escribir `src/frontend/auth.py`.
2. Validar el login e2e en la URL pública tras el redeploy de Luis.
