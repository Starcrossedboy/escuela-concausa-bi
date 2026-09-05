---
project: "FARO"
date: "2026-09-04"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — diagnóstico y fix de BUG-046 (el verifier OAuth rechaza todo id_token real por at_hash)"
touches: ["BUG-046", "US-402", "US-403", "REQ-004"]
tags: [devlog, bug, oauth, seguridad, at_hash, jwt, google, modo-reparacion]
---

# DevLog — 2026-09-04 — BUG-046: el verifier OAuth rechaza todo `id_token` real por `at_hash`

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

La cadena de login (US-402/US-403) estaba **desplegada y aparentemente lista**: `RealGoogleVerifier` en
`origin/main` (PR #194), credenciales OAuth cableadas en Cloud Run, `ANALISTA_EMAILS` cargado, consola de
Google configurada (test users + redirect_uri). `/auth/login` respondía 302 → Google y `/admin/*` sin
token respondía 401. Todo lo que se puede verificar **sin hacer login real** estaba en verde.

Pero el **primer login real fallaba con 401** — tanto para analista como para ciudadano. En los logs de
Cloud Run del servicio `faro.api.google` aparecía un `JWTClaimsError`. El bloqueo era total: **ningún
usuario podía autenticarse**, y por tanto era imposible demostrar el RBAC e2e (analista→200,
ciudadano→403) que pide AC-004.5.

## Causa raíz

`_verificar_id_token` (`src/api/security/google.py`) llamaba a `jwt.decode(...)` con firma RS256, `aud`,
`iss` y `exp`, pero **sin `access_token` y sin `options`**.

El `id_token` del **authorization code flow** de Google **siempre** incluye el claim `at_hash`.
`python-jose` trae `verify_at_hash=True` por defecto y, cuando encuentra `at_hash` en el token pero no le
pasan un `access_token` contra el cual compararlo, lanza:

```
JWTClaimsError("No access_token provided to compare against at_hash claim")
```

`verify()` traduce cualquier `JWTError` a un `ValueError` genérico y la capa HTTP lo convierte en un 401
uniforme (§5 del contrato). Resultado: **todo login real muere con 401**, exactamente el síntoma de prod.

`at_hash` es una defensa del **implicit flow**, donde el `id_token` viaja por el navegador y conviene atar
su integridad al `access_token`. En nuestro flujo **server-side** el `id_token` llega por un canal directo
servidor→Google sobre TLS y su integridad ya está garantizada por firma RS256 + `aud` + `iss` + `exp`.
Además **nunca usamos el `access_token`**: `_intercambiar_code` solo conserva el `id_token` y descarta el
resto. Es decir, `at_hash` no aporta seguridad aquí y su verificación por defecto solo introduce el fallo.

## Por qué los tests no lo cazaban

El fixture `google_falso` (`tests/test_oauth_google.py`) firma `id_token` reales en memoria, pero **emitía
sus tokens sin `at_hash`**. `at_hash` es precisamente el único claim que Google añade en producción y que
las pruebas nunca incluían, así que el camino con `at_hash` presente **jamás se ejercitaba** — 24 pruebas
de OAuth en verde y el bug intacto. Es el mismo patrón de BUG-044: el de-risk coincidía con prod porque
**ambos ejercían el mismo camino incompleto**.

## Fix (validado en local)

Una línea en el `jwt.decode` de `_verificar_id_token`, con un bloque de comentario que explica el porqué
para que nadie lo "arregle" quitándolo:

```python
options={"verify_at_hash": False},
```

**El resto de las verificaciones siguen activas**: firma RS256 contra el JWKS del `kid`, `aud == client_id`,
`iss` en la lista de emisores de Google, `exp` vigente, y `email_verified == true`. Solo se desactiva la
comprobación de `at_hash`, que no aplica al flujo server-side.

## Verificación

Ambiente: venv 3.11, `PYTHONPATH=.`, desde el worktree.

- **Prueba de regresión nueva** `tests/test_oauth_google.py::test_verifier_acepta_id_token_con_at_hash`:
  reusa `google_falso` añadiendo `at_hash` al `id_token` (el claim que Google siempre manda). Con el fix
  **pasa**; con el parche **revertido reprueba** con `ValueError: id_token invalido` y el log
  `JWTClaimsError` — **el mismo error de prod**. La prueba caza la clase de defecto, no la forma.
- **Familia completa de auth** (`test_auth_jwt`, `test_frontend_auth`, `test_oauth_google`,
  `test_puente_oauth_frontend`, `test_rbac`): **64 passed, 1 skipped**.
- **`vault_lint.py`**: ✅ Vault limpio.

## Propiedad y gobernanza (modo reparación)

- El fix toca `src/api/security/google.py`, que es **alcance C4 (Christian Ruiz)** y es un **cambio de
  seguridad** → cae bajo la **regla 7** (revisión humana explícita) y la **regla 9** (ownership).
- En **modo reparación** basta la **autorización de Luis Téllez (C5)** para preparar el fix; **el merge lo
  decide Edgar Coronel (PO)**. Yo (C5) diagnostiqué, apliqué y validé en local; **no mergeo**.
- El PR sale de `dev/luis-tellez` tocando `src/api/**` → **el check de ownership (`check_ownership.py`)
  fallará a propósito**. Es esperado: le señala a Edgar que este PR cruza alcance C4 y debe decidir el
  merge pese al check. Se **recomienda revisión de Christian Ruiz (C4)** por ser su módulo y ser seguridad.
- Precedente del mismo patrón: **BUG-041** y **BUG-008** (C5 diagnostica/parcha, el dueño de alcance o el
  PO cierran el merge).

## Estado y siguientes pasos

- **Local: cerrado.** Fix + regresión + registro de BUG-046 validados. `git diff --stat`:
  `google.py (+9)`, `test_oauth_google.py (+17)`, `Bug_Register.md (+86)` = 112 inserciones.
- **Pendiente de merge (Edgar).** El bug **sigue vivo en prod** hasta que el fix llegue a `main`.
- **Tras el merge — handoff C5 (yo):** sellar imagen `linux/amd64` desde `origin/main` y redesplegar con
  `gcloud run services update faro-api --image …` (patrón BUG-044/DEC-012: preserva env vars, secrets, SA
  y VPC; no re-inyecta `ANALISTA_EMAILS`, los correos siguen **efímeros**). Recién ahí el login real
  funciona y se puede correr la validación e2e de AC-004.5 (analista→200, ciudadano→403).
- **Nota:** `AUTH_LECTURA_PUBLICA` no está seteada en prod (default `True`), así que **la lectura pública
  no dependía de este bug** y siguió viva todo el tiempo. Este fix habilita el **login**, no la lectura.

---

*Cambio de código real (a diferencia de la operación de BUG-044): el fix, la prueba de regresión y el
registro del bug se prepararon en esta sesión bajo la autorización de Luis (modo reparación). Ningún correo
se versiona (Secrets_Policy); `ANALISTA_EMAILS` vive solo en la revisión de Cloud Run.*
