---
project: "FARO"
date: "2026-08-29"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1h"
touches: ["US-504", "REQ-005", "BUG-020", "DEC-5"]
tags: [devlog, cloud, devops, security, gcp]
---

# DevLog — 2026-08-29 — US-504: Provisionar la base GCP (Fase 1)

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

Aprovisionada en `faro-escuela-sensor` (us-central1) la **base segura del entorno
GCP** (Fase 1 del plan de Célula 5, Escenario B aprobado — DEC-5), como cimiento
para curar **BUG-020** en producción (Cloud Run hoy no tiene DB) en la Fase 2.

Recursos creados (todos verificados):

- **APIs habilitadas:** `compute`, `servicenetworking`, `sqladmin`, `vpcaccess`,
  `secretmanager` (antes deshabilitadas → confirmaba el diagnóstico de BUG-020).
- **Red privada:** VPC `faro-vpc` (custom) + subnet `faro-subnet` (10.10.0.0/24) +
  rango Private Services Access `google-managed-services-faro-vpc` (/16 → 172.21.0.0/16)
  + peering a `servicenetworking`.
- **Serverless VPC Access connector** `faro-connector` (10.8.0.0/28, e2-micro,
  min 2 / max 3) → permite que Cloud Run alcance la DB por **IP privada**.
- **Cloud SQL PostgreSQL** `faro-postgres`: `POSTGRES_16`, edition ENTERPRISE,
  tier `db-custom-1-3840` (1 vCPU / 3.75 GB, ~$50/mo), zonal, **IP privada
  172.21.0.3 y SIN IP pública** (`ipv4Enabled=false`), cifrado at-rest (default),
  **backups automáticos + PITR**. DB `faro` + usuario `faro_app`.
- **Secret Manager:** `jwt-secret-key`, `fernet-key`, `db-password` — generados con
  aleatoriedad criptográfica y almacenados directamente; **sus valores nunca se
  imprimieron ni se escribieron a disco**.
- **Service account de mínimo privilegio** `faro-api-sa`: `roles/cloudsql.client`,
  `roles/logging.logWriter` (a nivel proyecto) y `roles/secretmanager.secretAccessor`
  **por-secreto** (no project-wide). Sin llaves descargadas.
- **Audit logs (Data Access)** habilitados para `cloudsql` y `secretmanager`
  (merge que sólo añade `auditConfigs`, preservando los bindings existentes).

Todo el aprovisionamiento se capturó en un **script idempotente reproducible**
(`08_CICD_DevOps/scripts/provision-gcp-fase1.sh`): cada recurso se crea sólo si no
existe y re-ejecutarlo no desincroniza secretos ni la contraseña de la DB.

**Mapeo de seguridad:** cubre V2/V4 (creds fuera de texto plano → Secret Manager),
V6/V10 (cifrado at-rest, base para TLS), y CIS v8 controles 3, 5, 8, 11, 12.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code / claude-opus-4-8
- **Archivos creados/modificados:**
  - `08_CICD_DevOps/scripts/provision-gcp-fase1.sh` (nuevo, idempotente)
  - `_DevLog/2026-08-29-luis-tellez-us504-provision-gcp-fase1.md` (este)
  - `_DevLog/_index.md` (fila)
  - `02_Requirements/Traceability_Matrix.md` (evidencia US-504 en REQ-005)
  - `08_CICD_DevOps/_index.md` (referencia al script)
- **Decisiones autónomas del agente:** rangos IP sin traslape (subnet 10.10.0.0/24,
  connector 10.8.0.0/28, PSA auto 172.21.0.0/16); `secretAccessor` por-secreto en vez
  de project-wide; Data Access audit sólo en cloudsql/secretmanager (no allServices,
  por costo/ruido); reintento con `--edition=ENTERPRISE` al rechazar el default
  ENTERPRISE_PLUS el tier `db-custom-*`.
- **Correcciones manuales:** —
- **Prompt inicial:** "vamos a Fase 1" (go explícito de Luis; GCP estaba gated).

## Seguridad / calidad
- [x] Sin secretos hardcodeados (generados en runtime, jamás impresos ni versionados)
- [ ] Tests agregados/actualizados (infra; validación funcional va en Fase 2)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- BUG-020 **sigue abierto en producción** hasta Fase 2 (redeploy del API con
  conexión a Cloud SQL vía el connector + secretos + service account).
- Gold aún no existe en Cloud SQL (se puebla en Fase 2).

## Próximos pasos (Fase 2 — gated, requiere "go")
1. Poblar Gold en Cloud SQL (`faro`) reusando la vía documentada por Diana
   (fixtures Bronze + `dbt build` acotado).
2. Redesplegar `faro-api` en Cloud Run con: `--service-account=faro-api-sa`,
   `--vpc-connector=faro-connector`, `--set-secrets` (JWT/Fernet/DB) y variables de
   conexión a la IP privada → **curar BUG-020 en prod**.
3. Verificar `/api/v1/escuelas` → 200 contra Cloud SQL.
