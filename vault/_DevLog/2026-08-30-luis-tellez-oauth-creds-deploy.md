---
project: "FARO"
date: "2026-08-30"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — crear credenciales OAuth de Google y cablearlas en Cloud Run (desbloquea el login de C4)"
touches: ["US-402", "US-403", "REQ-005", "REQ-004"]
tags: [devlog, cloud, devops, cloud-run, oauth, seguridad, secret-manager]
---

# DevLog — 2026-08-30 — Credenciales OAuth de Google cableadas en Cloud Run (parte deploy/C5)

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/08_CICD_DevOps/Cloud_Run_Deploy|Cloud_Run_Deploy §4.5]] · [[vault/03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt|ADR-004]]

## Contexto

El núcleo OAuth2/JWT de C4 (**US-402**, Christian Ruiz) ya está en `main`: `RealGoogleVerifier`,
el flujo `/auth/login` → Google → `/auth/callback`, y el RBAC de 2 roles con el flag híbrido
`AUTH_LECTURA_PUBLICA` (**US-403**). Pero el login **no podía completarse en prod** porque faltaba
lo que es responsabilidad de **C5 (deploy)**: un **cliente OAuth real de Google** y el cableado de
sus credenciales en Cloud Run. Sin `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI`,
`RealGoogleVerifier` levanta `GoogleNotConfigured` y el callback responde 500. Crear esas credenciales
es la dependencia **D-A** del plan de S5 y desbloquea a C4 para cerrar la verificación de identidad.

**Fuera de alcance de esta entrega:** el flip de `AUTH_LECTURA_PUBLICA=true → false` (la lectura sigue
pública para la demo) y la implementación del verifier en sí, ambos de C4. Aquí sólo se **habilitan**
las credenciales y se deja el login listo para que C4 lo cierre.

## Qué se hizo (parte C5 · Cloud & DevOps)

- **Cliente OAuth Web creado en Google Cloud Console** (`faro-api-web`, acción manual de Luis — la
  consola es la única vía para este caso; `gcloud iap oauth-*` sólo crea marcas IAP internas, que no
  aplican). Redirect autorizado = la URL **canónica** del servicio:
  `https://faro-api-eanzfglvyq-uc.a.run.app/api/v1/auth/callback` (evita `redirect_uri_mismatch`).
- **Pantalla de consentimiento: External + modo "Prueba" (Testing).** El proyecto vive en una org
  **personal** (`luis-g-roses-org`), así que "Internal" sólo dejaría entrar al dominio de Luis y
  excluiría a los 20 del equipo + evaluadores. Testing admite hasta 100 test users, no exige
  verificación de Google (los scopes `openid email profile` no son sensibles) y basta con dar de alta
  cada correo como usuario de prueba. **DEC:** D-A.1 = External+Testing; D-A.4 = redirect canónico.
- **`GOOGLE_CLIENT_SECRET` guardado en Secret Manager** como secreto `google-client-secret` (creado por
  Luis; **el valor nunca pasó por el agente, los logs ni el repo**). Verificado que existe y que la
  revisión lo consume como `secretKeyRef`.
- **`deploy-cloud-run.sh` cableado** (único archivo de código del PR):
  - `GOOGLE_CLIENT_ID` y `GOOGLE_REDIRECT_URI` como **env vars** (son públicos: viajan en la URL de
    consentimiento del navegador).
  - `GOOGLE_CLIENT_SECRET=google-client-secret:latest` añadido a `--set-secrets` (Secret Manager en
    runtime, nunca env plano → coherente con `vault/07_Security/Secrets_Policy.md`).
  - Bloque **comentado** `ANALISTA_EMAILS` documentando la allowlist del rol `analista` (US-403):
    dueño pendiente (PO/Edgar, `task_0c696e2e`), hoy vacío ⇒ todos `ciudadano`, y el comando para
    setearlo **efímero sin versionarlo** cuando C4 cierre el verifier. No se versiona ningún correo.
- **Redeploy aplicado** (misma imagen, sólo config) → revisión **`faro-api-00007-4dd`** sirviendo 100%
  del tráfico.
- **`Cloud_Run_Deploy.md` §4.5:** documentado el cableado OAuth (env públicos vs. secreto) y el flujo
  de validación manual del login + carga efímera de test users.

## Validación en prod (norma: validar lo desplegado ANTES del commit/PR)

- Revisión viva **`faro-api-00007-4dd`** con las 3 piezas cableadas, verificado con
  `gcloud run services describe`:
  - `GOOGLE_CLIENT_ID` y `GOOGLE_REDIRECT_URI` presentes como **env vars** (valor visible, son públicos).
  - `GOOGLE_CLIENT_SECRET` presente como **`secretKeyRef` → `google-client-secret`** (Secret Manager,
    no texto plano), junto a `JWT_SECRET_KEY` y `POSTGRES_PASSWORD` que ya venían así de Fase 2.
- **Login e2e (manual):** `/api/v1/auth/login` redirige a la pantalla de consentimiento de Google, se
  acepta con un test user dado de alta, Google regresa al callback. El callback responde **401**
  (`{"error":"unauthorized", ...}`), **no 500** — que es exactamente lo esperado: prueba que las
  credenciales están bien cableadas (ya no hay `GoogleNotConfigured` → 500) y que lo que falta es la
  implementación de `RealGoogleVerifier.verify()`, que es **de C4**. El error genérico confirma además
  que el handler no filtra detalle interno.
- `/api/v1/health` → 200 y `/api/v1/escuelas` → 200 con 25 escuelas (sin regresión de Fase 2/BUG-020).
- `vault_lint.py` verde; diff sin secretos (sólo el `client_id`, que es público).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos:** `vault/08_CICD_DevOps/scripts/deploy-cloud-run.sh`, `vault/08_CICD_DevOps/Cloud_Run_Deploy.md` (§4.5),
  este DevLog, `vault/_DevLog/_index.md`, `vault/02_Requirements/Traceability_Matrix.md`.
- **Acción manual de Luis (prohibida al agente):** crear el cliente OAuth y la pantalla de
  consentimiento en la consola, y cargar `GOOGLE_CLIENT_SECRET` en Secret Manager. El agente nunca vio
  el secreto.
- **Operación GCP (sin diff):** `gcloud run deploy` (misma imagen, config nueva) → revisión
  `faro-api-00007-4dd`. Ejecutado con "go" explícito de Luis (regla GCP gated).
- **Decisión:** habilitar sólo las credenciales y dejar el login listo, **sin** tocar
  `AUTH_LECTURA_PUBLICA` (sigue `true`, lectura pública para la demo). El flip a `false` y la
  implementación del verifier quedan gated por C4.

## Bloqueantes / avisos a otros owners

- **Christian (C4) — desbloqueado:** las credenciales OAuth ya están vivas en prod. Falta implementar
  `RealGoogleVerifier.verify()` (hoy levanta `NotImplementedError` tras validar el `client_id`) y,
  cuando el login e2e funcione, coordinar conmigo el flip `AUTH_LECTURA_PUBLICA=false`.
- **Edgar (PO) — allowlist del rol `analista` (US-403):** definir el dueño y el contenido de
  `ANALISTA_EMAILS` (`task_0c696e2e`). Hoy vacío ⇒ todos `ciudadano`. El deploy script ya deja el hook
  comentado con el comando para setearlo efímero (sin versionar correos).
- **Recordatorio de trazabilidad:** actualizar `_index.md`, la matriz (REQ-005/US-402) y este DevLog
  antes del push — hecho en este PR.
