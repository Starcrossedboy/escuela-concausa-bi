---
project: "FARO"
date: "2026-09-03"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "1 sesión — puente OAuth → Streamlit y sesión de FARO Web (US-405)"
touches: ["US-405", "US-402", "REQ-004", "ADR-010", "SEC-007", "SEC-008"]
tags: [devlog, celula-4, api, frontend, oauth2, seguridad, us405]
---

# DevLog — 2026-09-03 — Puente OAuth → frontend y sesión de FARO Web (US-405)

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/03_Architecture/ADRs/ADR-010-puente-oauth-frontend|ADR-010]] ·
[[vault/03_Architecture/API_Specification|API_Spec §2.1.2]] · [[vault/07_Security/Security_Audit_Log|SEC-007, SEC-008]]

## Contexto

US-405 estaba bloqueada por una pieza de diseño que nunca se escribió. `Frontend_Architecture.md` §3
decía que el front *"guarda el access/refresh token en `st.session_state`"* pero no **cómo llega**:
`/auth/callback` respondía el `TokenPair` como JSON al **navegador**, no al servidor de Streamlit. La
persona veía un blob de JSON y el front nunca se enteraba del login.

La solución obvia —redirigir con el token en la query string— es la mala: la URL queda en el
historial del navegador, en los logs de cualquier proxy y en la cabecera `Referer`. Y la solución
limpia —cookies `HttpOnly`— no sirve porque **Streamlit no puede leer cookies** sin un componente de
terceros.

Decisión tomada con el PO: **código de un solo uso**. Documentada en ADR-010 con las cuatro
alternativas descartadas y su costo.

## Qué se hizo

### API (🟢 `src/api/**`)

- **`/auth/login?redirect=`** con **allowlist estricta** (`FRONTEND_REDIRECT_URIS`) y comparación
  **exacta**, no por prefijo: un `startswith` deja pasar `http://localhost:8501.evil.tld`. Un open
  redirect dentro del flujo de login es el vehículo clásico para desviar el código de autorización.
  El destino viaja **dentro del `state` firmado**, así que Google lo devuelve intacto y nadie lo
  altera por el camino.
- **`/auth/callback` bifurca**: con `redirect`, 302 al front con `?code_faro=<código>`; sin él, el
  `TokenPair` como JSON igual que antes (compatibilidad con clientes no-navegador y pruebas).
- **`POST /auth/exchange`** canjea el código por el par de JWT, **re-resolviendo el rol** con la
  política vigente en vez de confiar en el guardado.
- **`src/api/security/codigos_login.py`** (nuevo). Tres decisiones que lo sostienen:
  - **No se guardan tokens, se guarda la identidad.** Los JWT se emiten al canjear ⇒ cero
    credenciales en reposo.
  - **Del código solo el SHA-256.** Quien lea la tabla no puede canjear nada, igual que con una
    contraseña.
  - **`DELETE ... RETURNING`**: borrar y leer son la misma operación, así que el "un solo uso" lo
    garantiza Postgres y no una comprobación en Python que dos peticiones simultáneas esquivarían.
  - La tabla vive en su propio esquema **`auth`**, fuera de `gold`: no es un artefacto analítico y
    no le corresponde a la Célula 1.

### Frontend (🟡 `src/frontend/auth.py`, autorizado por escrito por Manuel)

`current_user()` recoge el `?code_faro` de `st.query_params`, lo canjea **desde el servidor** y
guarda la sesión. Las páginas no saben nada del flujo OAuth: siguen llamando `current_user()`,
`login_button()`, `logout_button()` y `require_role()` con la misma firma de antes. `access_token`
queda en `st.session_state["access_token"]`, que es donde `pages/3_Chat.py` ya lo busca (US-305) —
hay una prueba que lo fija para que nadie lo mueva.

El código se borra de la URL **pase lo que pase**: si se queda, recargar la página falla (es de un
solo uso) y parece un error del sistema sin serlo.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5.
- **Creados:** `src/api/security/codigos_login.py`, `tests/test_puente_oauth_frontend.py` (15 casos),
  `tests/test_frontend_auth.py` (12 casos), `vault/03_Architecture/ADRs/ADR-010-puente-oauth-frontend.md`,
  este DevLog.
- **Modificados:** `src/api/v1/auth.py`, `src/api/config.py`, `src/api/schemas.py`,
  `src/api/security/jwt.py`, `src/frontend/auth.py`, `src/frontend/README.md`, `.env.example`,
  `api/openapi.v1.json`, `vault/03_Architecture/API_Specification.md` (§2.1.2, §3.2, §7),
  `vault/03_Architecture/ADRs/_index.md`, `vault/07_Security/Security_Audit_Log.md`,
  `vault/_DevLog/_index.md`, `vault/02_Requirements/Traceability_Matrix.md`.
- **Revisión manual:** revisado línea por línea. El foco estuvo en tres cosas: que la allowlist no se
  pueda burlar por prefijo, que ninguna URL del flujo lleve algo parecido a un token (hay prueba
  explícita que busca `eyJ`), y que el código sea opaco y no transporte identidad.

## Seguridad / calidad

- [x] **27 pruebas nuevas.** `pytest` sobre API + frontend → **131 passed** (ver salvedad abajo)
- [x] `ruff check src tests` → limpio
- [x] Ninguna credencial viaja por la URL — cubierto por prueba
- [x] Allowlist del redirect probada con el caso del sufijo (`...8501.evil.tld` → 400)
- [x] Código de un solo uso, expiración y 401 sin fuga, probados
- [ ] Suite completa: la corre el CI (esta máquina no tiene el ambiente 3.11 de C1/C3)

## Bloqueantes / avisos a otros owners

- **Manuel (C2):** `src/frontend/auth.py` implementado con la firma que acordamos; tu `app.py`,
  `1_Dashboards.py` y `superset_client.py` **no cambian**. Necesito de ti la URL real del front
  desplegado para la allowlist. **Y un aviso:** `tests/test_frontend_dashboards_streamlit.py::test_con_guest_token_rechazado_no_hay_tableros_ni_filtros`
  me falla en local — pero **falla igual en `main` sin mis cambios**, así que no lo causé. Mi venv
  tiene `streamlit 1.63.0` y el proyecto pinea `1.62.0`, así que sospecho deriva de versión. Verifícalo
  con el pin.
- **Luis (C5) — dos cosas nuevas, además del redeploy pendiente:**
  1. `FRONTEND_REDIRECT_URIS` debe llevar la URL real del front en el despliegue, o el login
     responde 400.
  2. **`SEC-007`:** el almacén crea su tabla al arrancar, así que el rol de la aplicación necesita
     permiso de `CREATE`. Si no lo tiene, degrada a memoria y lo grita en el log — y en memoria el
     login **solo es correcto con una instancia**. Es lo primero que hay que revisar en los logs tras
     el redeploy.
- **`SEC-008` (nuevo, de la superficie de C2):** FARO Web autentica contra Superset con la credencial
  **admin** para emitir guest tokens. Es consecuencia directa de la decisión de arquitectura (el
  front habla directo con Superset), así que no la cuestiono — pero corresponde registrarla, y la
  mitigación es un usuario de Superset con permisos mínimos en vez de `admin`. C5 provisiona, C2
  consume.
- **Regla 7:** cambio de seguridad → revisión humana explícita en el PR.

## Próximos pasos

1. Validar el login e2e en la URL pública tras el redeploy, y revisar los logs por `SEC-007`.
2. Pruebas integrales de seguridad contra el desplegado (roles, tokens, endpoints protegidos).
3. Decidir con Luis el flip de `AUTH_LECTURA_PUBLICA` una vez cargados los *test users*.
