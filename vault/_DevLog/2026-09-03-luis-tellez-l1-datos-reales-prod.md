---
project: "FARO"
date: "2026-09-03"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — L1 «Piso RISK-001»: datos reales + OAuth real + RBAC vivos en la URL pública"
touches: ["US-505", "US-402", "US-403", "RISK-001", "BUG-035", "REQ-005", "REQ-004"]
tags: [devlog, deploy, cloud-run, cloud-sql, gold, oauth, rbac, prod]
---

# DevLog — 2026-09-03 — L1: datos reales, OAuth real y RBAC vivos en prod

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

La URL pública ya estaba viva desde US-505 Fase 2, pero servía la imagen `dev` (sin sellar) y con
**Gold vacío** en Cloud SQL: `/kpis` sin números reales, `/municipios` **500** (BUG-035), `/version`
siempre `"dev"`, y el diferenciador prescriptivo sin datos que mostrar. **L1** es el «Piso RISK-001»:
subir el Gold **real** ya materializado, sellar la imagen de `main` (que trae OAuth real + el fix de
`/municipios`) y dejar RBAC cableado. **Local-first respetado**: el Gold que se sube es byte-idéntico al
de-risk local ya verificado (no se corre dbt/ML contra Cloud SQL, que es solo-IP-privada).

Autorizado por Luis en dos pasos: **«Ir a GCP (L1)»** y, tras validar el despliegue, **«Sí, con el
correo de Edgar»** para activar el rol `analista`. El agente **no mergea ni hace push a `main`**; este
DevLog acompaña el PR a Edgar (L1.6).

## Qué se hizo

- **L1.1 — Gold → GCS.** `pg_dump` **solo tablas** del Gold de `escuela_real` (10: `dim_driver`,
  `dim_escuela`, `dim_municipio`, `dim_tiempo`, `fact_escuela_ciclo`, `features_escuela`,
  `geo_municipio`, `matricula_municipio_nivel`, `predicciones`, `recomendaciones`; **0 matviews** — los
  9 cubos son L2/Superset y referencian silver/bronze ausentes en el import) → 59 MB SQL plano → **bucket
  privado** `gs://faro-escuela-sensor-sql-import` (`uniform-bucket-level-access` +
  `public-access-prevention`) + rol `roles/storage.objectViewer` al **SA de la instancia** Cloud SQL.
- **L1.2 — import a Cloud SQL.** `gcloud sql import sql faro-postgres gs://…/dumps/gold_real.sql
  --database=faro --user=faro_app` → **exit 0**. Es server-side, así que funciona con la instancia de
  **solo IP privada** (no necesita Auth Proxy ni IP pública); `--user=faro_app` para que dropee/cree sus
  propias tablas sin GRANTs extra.
- **L1.3 — rebuild `linux/amd64` + redeploy.** `build-and-push.sh` construye **sin `--platform`** → desde
  la Mac (arm64) la imagen **no arranca** en Cloud Run. Se reconstruyó con
  `docker buildx build --platform linux/amd64 --build-arg GIT_SHA=e8ec818…` desde un **contexto limpio de
  `origin/main`** (`git archive` a `/tmp/faro-build-main`; el worktree estaba 13 commits atrás y sucio) →
  push a `us-central1-docker.pkg.dev/faro-escuela-sensor/faro-images/faro-api:e8ec818…` → redeploy con
  `deploy-cloud-run.sh e8ec818…` → revisión **`faro-api-00008-nrj`** al 100% del tráfico.
- **Único cambio de código** (va en este PR): **`vault/08_CICD_DevOps/scripts/deploy-cloud-run.sh`** —
  se activa `ANALISTA_EMAILS="${ANALISTA_EMAILS:-}"` (leída del entorno) y se añade a `--set-env-vars`.
  **No se versiona ningún correo**: el del PO se inyecta **efímero** al invocar el script
  (`ANALISTA_EMAILS=<correo> ./deploy-cloud-run.sh`), queda solo en la revisión de Cloud Run, nunca en
  el repo (Secrets_Policy). El comentario usa el placeholder `<correo-del-analista>`.

## Validación en prod (todo GREEN)

`BASE=https://faro-api-eanzfglvyq-uc.a.run.app`

- `/api/v1/version` → **`e8ec818…`** (ya no `"dev"`; sella qué imagen corre).
- `/api/v1/kpis` → matrícula **20,638,574** (idéntica al de-risk local), variación **−1.81%** (el `dev`
  daba **−5.39%** por el fix de KPI-02 que sí trae `main`), completitud **0.1969**.
- `/api/v1/municipios` → **200** con municipios reales — **BUG-035 cerrado en prod** por el rebuild (el
  fix ya estaba en `main`, PR #183; la imagen `dev` no lo tenía).
- `/api/v1/auth/login` → **302 → Google** con `state` **JWT real** de un solo uso + cookie
  `HttpOnly`/`Secure` — **US-402 OAuth real VIVO** (deja de responder `state=faro`).
- **RBAC (AC-004.4):** `/api/v1/admin/export` y `/api/v1/admin/metrics` → **401** sin token; lectura
  pública (`/kpis`, `/escuelas`, `/municipios`) → **200** sin token (URL viva para el evaluador,
  `AUTH_LECTURA_PUBLICA=true`).
- **Diferenciador prescriptivo (el corazón del proyecto), confirmado en vivo:**
  `/predicciones/09DBN0007I` → `driver_dominante:"D1"` → *«Priorizar programas de becas y apoyo
  alimentario…»*; `/predicciones/09DAL0009J` → `driver_dominante:"D2"` → *«Coordinar con seguridad
  pública rutas escolares seguras…»*. Dos escuelas de riesgo parecido, **recomendación distinta** según
  el driver.

**Cierra:** RISK-001 (datos reales en la URL pública) · US-402 (OAuth real en prod) · RBAC AC-004.4
(Edgar → `analista` al iniciar sesión con su cuenta Google).

## Hallazgos / caveats

- **Primer login del PO (no verificable headless):** para que el round-trip complete, el redirect URI
  `…/api/v1/auth/callback` debe estar dado de alta como *Authorized redirect URI* en la consola OAuth de
  Google. `/auth/login` ya responde **302** con `state` real; si al entrar el PO ve `redirect_uri_mismatch`,
  se añade esa URI en la consola (config de C4/PO). **No bloquea** la URL pública ni los datos.
- `escuelas_en_riesgo=0` (máx `indice_riesgo` 0.401 < umbral 0.6) es el hallazgo **H1** (C2), ajeno a L1.
- El `CMD` del Dockerfile en forma shell (warning `JSONArgsRecommended`) es **preexistente**, fuera de
  alcance; **no se tocó**.

## Seguridad / alcance

- Territorio C5: `vault/08_CICD_DevOps/scripts/**`. **Cero credenciales y cero correos versionados**;
  `JWT_SECRET_KEY`, `POSTGRES_PASSWORD` y `GOOGLE_CLIENT_SECRET` siguen en **Secret Manager**
  (`--set-secrets`), nunca en la imagen ni en env plano.
- Cambios en GCP: nueva **revisión** + **imagen** amd64 + **dato real** en Cloud SQL — todos reversibles
  (redeploy de la revisión previa / reimport). Sin cambios de esquema.

## Qué falta (fuera de este PR)

- **L1.6 = este PR** (a Edgar; el PO mergea). Coordinación pendiente: H1–H4 con sus dueños y el
  agente/L4 (US-405) con C3 (deps + LLM + rol read-only + deploy del frontend).
