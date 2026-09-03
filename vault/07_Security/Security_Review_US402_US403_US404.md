---
id: DOC-SECREV-C4
title: "Revisión de seguridad — cierre de US-402, US-403 y US-404"
owner: "Christian Imanol Ruiz Hurtado"
status: in_review
version: "1.0"
source_of_truth: true
traces_up: ["REQ-004", "vault/07_Security/Security_Review_Checklist", "vault/_Meta/Vault_Rules"]
traces_down: ["US-402", "US-403", "US-404", "US-405", "SEC-002", "SEC-003", "SEC-004", "SEC-005", "SEC-006"]
last_reviewed: "2026-09-02"
tags: [security, review, oauth2, jwt, rbac, hardening, celula-4]
---

# Revisión de seguridad — cierre de US-402, US-403 y US-404

> **Regla 7 del vault:** todo cambio de seguridad requiere revisión humana explícita del dueño del
> área. Este documento **es** ese registro para la superficie de autenticación y autorización de la
> API. Lo firma Christian Imanol Ruiz Hurtado (Tech Lead C4, dueño de `vault/07_Security/**`).
> → [[vault/07_Security/_index]] · [[vault/07_Security/Security_Review_Checklist]] ·
> [[vault/03_Architecture/API_Specification]] · [[vault/07_Security/Security_Audit_Log]]

## 1. Alcance

| Historia | Qué cubre | Estado tras esta revisión |
|---|---|---|
| `US-402` | OAuth2 con Google + JWT propio (access/refresh) | ✅ cerrada — se implementó la verificación real del `id_token` y el `state` anti-CSRF |
| `US-403` | RBAC de 2 roles (`ciudadano` / `analista`) | ✅ cerrada con **una salvedad abierta**: la política `ANALISTA_EMAILS` es del PO (ver §5) |
| `US-404` | Hardening: rate limiting, CORS, validación estricta, errores sin fuga | ✅ cerrada con **dos follow-ups aceptados** (RS256 y rotación de refresh, §5) |
| `US-405` | Login/logout y vistas por rol en FARO Web | ⛔ **no** cubierta aquí: vive en `src/frontend/**`, cuyo dueño es Manuel Serranía (C2) |

Lo que **no** entra: la política de producto sobre quién es `analista`, el flip de
`AUTH_LECTURA_PUBLICA` en el entorno desplegado (C5) y el frontend.

## 2. Qué se corrigió en esta revisión

### 2.1 El `state` de OAuth era una constante (`SEC-002`)

`GET /auth/login` mandaba a Google el literal `state=faro`. Un `state` constante **no protege de
nada**: cualquiera podía reproducirlo y forjar una llamada a `/auth/callback` con un `code` propio,
que es exactamente el ataque de *login CSRF* que el parámetro existe para impedir. Era observable
desde fuera, sin credenciales, en la URL pública.

**Corregido.** El `state` ahora es un JWT propio de 10 minutos con `nonce` aleatorio, que viaja por
dos canales independientes: el parámetro de la URL de Google y la cookie de primera parte
`faro_oauth_state` (`HttpOnly`, `Secure` fuera de local, `SameSite=Lax`, un solo uso). El callback
exige que ambos existan, coincidan (`secrets.compare_digest`) y que el token sea válido y vigente;
si no, **401** uniforme, sin decir cuál de las tres condiciones falló.

Se eligió un `state` firmado y no uno en memoria del servidor porque Cloud Run corre varias
instancias sin estado compartido: un `state` en RAM se perdería entre la ida y la vuelta del
navegador. Detalle en [[vault/03_Architecture/API_Specification]] §2.1.1.

### 2.2 La identidad de Google no se verificaba de verdad

`RealGoogleVerifier.verify()` levantaba `NotImplementedError`: el login **no podía completarse** ni
siquiera con las credenciales que C5 dejó vivas en Cloud Run el 30-ago (revisión `faro-api-00007-4dd`).

**Implementado** el *authorization code flow* completo:

1. `POST` al *token endpoint* con `code`, `client_id`, `client_secret` y `redirect_uri`.
2. Verificación del `id_token`: firma **RS256** contra la llave del JWKS público de Google que
   corresponde al `kid` del encabezado, `aud == GOOGLE_CLIENT_ID`, `iss` de Google y `exp` vigente.
   La lista de algoritmos se pasa **explícita** — nunca se confía en el `alg` del token entrante
   (*algorithm confusion*).
3. Se exige `email_verified == true`: el rol se resuelve por correo, así que un correo sin verificar
   permitiría suplantar a un futuro `analista` registrando esa dirección en otro proveedor.

El módulo **no registra ni devuelve** el `code`, el `client_secret` ni el `id_token`; todo fallo del
intercambio se convierte en un `ValueError` genérico que la capa HTTP traduce a **401** uniforme.

## 3. Checklist ejecutado

| Punto de [[vault/07_Security/Security_Review_Checklist]] | Veredicto | Evidencia |
|---|---|---|
| Auth aplicada en endpoints no públicos (401 sin token) | 🟢 | `tests/test_rbac.py`, `tests/test_auth_jwt.py`; `/auth/me` → 401 en la URL pública |
| Autorización por rol (403 con token válido pero rol corto) | 🟢 | `tests/test_rbac.py` — matriz 401/403/200 sobre `/admin/*` |
| Validación/sanitización de entrada | 🟢 | `EntradaEstricta` (`extra="forbid"`) en los 4 modelos de entrada → 422; SQL del agente pasa por `preparar_sql_seguro` |
| Sin secretos hardcodeados | 🟢 | Todo por `Settings`; el `client_secret` vive en Secret Manager (C5) |
| Sin fuga de información en errores | 🟢 | `ErrorOut` uniforme; el 500 registra en log y devuelve mensaje genérico (`tests/test_hardening.py`) |
| Rate limiting en endpoints sensibles | 🟡 | Activo (`120/minute` por IP+path) pero **en memoria por proceso** → `SEC-003` |
| Logs sin datos personales | 🟢 | Se registra el tipo de excepción y el `request_id`, nunca el `code`, el token ni el correo |
| CSRF en el flujo OAuth | 🟢 | Corregido en esta revisión (§2.1), `tests/test_oauth_google.py` |
| Algoritmo de firma de los JWT propios | 🟡 | HS256 simétrico → `SEC-004` |
| Ciclo de vida del refresh token | 🟡 | Sin rotación ni revocación → `SEC-005` |
| SCA / dependencias | ⬜ | No ejecutado en esta sesión; corresponde al gate de CI (C5) |

**Veredicto global: 🟡** — sin hallazgos bloqueantes abiertos; cuatro riesgos residuales aceptados y
registrados, con dueño y condición de cierre.

## 4. Pruebas que sostienen el veredicto

| Archivo | Casos | Qué prueba |
|---|---|---|
| `tests/test_oauth_google.py` | 18 | `state` (roundtrip, no reutilizable como access, cookie `HttpOnly`, sin `state` → 401, sin cookie → 401, `state` ajeno → 401, un solo uso) y `RealGoogleVerifier` contra un Google falso con llave RSA en memoria: audiencia ajena, emisor ajeno, token expirado, `kid` desconocido, correo no verificado, rechazo de Google → 401 sin fuga |
| `tests/test_auth_jwt.py` | 16 | Núcleo JWT, política de rol y `/auth/*` (el callback ahora ejercita el flujo `login → callback` completo) |
| `tests/test_rbac.py` | 10 | Matriz 401/403/200 y ambas ramas de `AUTH_LECTURA_PUBLICA` |
| `tests/test_hardening.py` | 7 | CORS, 429 con `ErrorOut`, 422 por campo extra, 500 sin fuga |

Ejecutado: `pytest tests/test_oauth_google.py tests/test_auth_jwt.py tests/test_rbac.py
tests/test_hardening.py tests/test_api_contract.py -q` → **79 passed**. `ruff check src/api tests` →
limpio.

> Nota de honestidad: la suite completa del repositorio **no** se corrió en esta sesión — la máquina
> no tiene el ambiente 3.11 con las dependencias de las Células 1 y 3 (Great Expectations, MLflow).
> Lo verifica el CI.

## 5. Riesgos residuales aceptados (registrados en el Security Audit Log)

| ID | Hallazgo | Severidad | Dueño del cierre | Condición de cierre |
|---|---|---|---|---|
| `SEC-002` | `state` de OAuth constante (`faro`) | high | Christian Ruiz | ✅ **resuelto** en esta revisión |
| `SEC-003` | Rate limiting en memoria por proceso: con varias instancias de Cloud Run el límite real se multiplica por el número de instancias | medium | Luis Téllez (C5) + Christian | Backend compartido (Redis) o límite en el balanceador. Aceptado para la demo: hoy corre 1 instancia |
| `SEC-004` | JWT propios firmados con **HS256** (secreto simétrico): quien pueda leer `JWT_SECRET_KEY` puede **emitir** tokens, no solo verificarlos | medium | Christian + C5 (llaves) | Migrar a RS256 con par de llaves en Secret Manager. Aceptado: el secreto ya vive en Secret Manager y no sale de ahí |
| `SEC-005` | Refresh tokens sin rotación ni revocación: un refresh filtrado sirve 7 días y no hay forma de invalidarlo | medium | Christian | Rotación en cada canje + lista de revocación. Aceptado para la ventana del proyecto |
| `SEC-006` | `AUTH_LECTURA_PUBLICA=true` en el entorno desplegado: la lectura de datos no exige sesión | low (decisión de producto) | Luis Téllez (C5) | Poner `false` cuando el login e2e esté validado en vivo. Es un **interruptor de configuración**, no un cambio de código |

## 6. Pendientes que **no** son míos

- **Edgar (PO):** ratificar `ANALISTA_EMAILS` — quién es `analista`. Hoy la allowlist está vacía, así
  que **todos** son `ciudadano` (mínimo privilegio). US-403 no puede darse por cerrada de producto
  hasta que exista esa decisión, aunque el mecanismo esté completo y probado.
- **Luis Téllez (C5):** dar de alta a los evaluadores como *test users* de la pantalla de
  consentimiento (está en modo Testing) y, tras validar el login en vivo, coordinar el flip de
  `AUTH_LECTURA_PUBLICA`.
- **Manuel Serranía (C2):** `src/frontend/**` — US-405 consume este flujo desde FARO Web.
- **Edgar (PO):** `vault/03_Architecture/ADRs/**` **no tiene dueño en `ownership.yml`**, así que nadie
  puede actualizar `ADR-004` sin que el gate de propiedad repruebe el PR. Los cambios de §2 de este
  documento deberían reflejarse ahí.

## 7. Firma

| | |
|---|---|
| **Revisor** | Christian Imanol Ruiz Hurtado — Tech Lead C4, dueño de `vault/07_Security/**` |
| **Fecha** | 2026-09-02 |
| **Veredicto** | 🟡 Aprobado con riesgos residuales aceptados (§5) |
| **Asistencia de IA** | Claude Code / claude-opus-5 — código revisado línea por línea antes de commitear ([[vault/_DevLog/2026-09-02-christian-ruiz-us402-cierre-oauth-e2e]]) |
