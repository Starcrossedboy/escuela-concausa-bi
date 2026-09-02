---
project: "FARO"
date: "2026-08-30"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — cierre formal del Sprint S4 (Célula 5 · Cloud & DevOps): consolidación, validación de prod y retro de dependencias"
touches: ["US-502", "US-504", "US-505", "REQ-005", "BUG-020", "BUG-025", "META-RULES"]
tags: [devlog, cloud, devops, cierre-sprint, retro, seguridad]
---

# DevLog — 2026-08-30 — Cierre de Sprint S4 (Célula 5 · Cloud & DevOps)

→ [[_DevLog/_index|Volver al índice]] · [[02_Requirements/Traceability_Matrix|Traceability Matrix · REQ-005]] · [[08_CICD_DevOps/Cloud_Run_Deploy|Cloud_Run_Deploy]]

## Contexto

Último día del **Sprint S4** (2026-08-24 → 2026-08-30). Esta entrada **no agrega código nuevo**:
consolida lo entregado por la Célula 5 en S4 —cada hito ya tiene su propio DevLog— deja
**evidencia de validación de prod fechada al 2026-08-30** y registra la **retro de dependencias**
(dónde el equipo depende hoy de C5) como insumo para el PO de cara al CODE FREEZE (6-sep) y la
demo (9-sep).

## Lo entregado por C5 en S4 (todo MERGEADO en `main`)

| PR | Historia | Resultado |
|---|---|---|
| #138 | US-502 (Fase 0) | Compose sin `container_name` → soporta worktrees; verificación agnóstica; **BUG-020 curado end-to-end en LOCAL** |
| #141 | US-504 (Fase 1 GCP) | Base GCP en `faro-escuela-sensor`: VPC privada + connector, **Cloud SQL IP privada** + backups/PITR, Secret Manager, SA de mínimo privilegio, audit Data Access |
| #144 | US-505 (Fase 2) | Gold poblado en Cloud SQL + redeploy por IP privada con secretos en Secret Manager → **BUG-020 curado en PROD** y cerrada la violación de `JWT_SECRET_KEY` en texto plano |
| #146 | US-502/US-504 (docs seguridad) | `Credentials_Policy` v1.1 (mapeo **CIS v8** corregido), `Threat_Model` v1.0.1 (US IDs reconciliados + tech GCP), `generate-keys.py` sin dependencia de `cryptography` + `JWT_SECRET_KEY` |
| #148 | BUG-025 (parte deploy/C5) | Rebuild `linux/amd64` `v0.2.2-bug025` + redeploy → `/agente/consulta` deja de ser el stub (degrada seguro); config de Fase 2 preservada |

**Efecto de rúbrica:** con la URL pública sirviendo datos reales, **RISK-001 queda mitigado de facto**
(el techo de 6.0 por "sin URL viva" ya no aplica) y **BUG-020 está curado en prod**.

## Validación en prod (norma: validar lo desplegado ANTES de cerrar/commitear)

`https://faro-api-526490367142.us-central1.run.app` — corrida 2026-08-30:

- `/api/v1/health` → **200** `{"status":"ok"}`.
- `/api/v1/escuelas` → **200 con 25 escuelas** (sin regresión de BUG-020).
- `/api/v1/predicciones/{cct}` → **404 estructurado** `{"error":"not_found",…,"request_id":…}` (correcto:
  ML aún no publica a `gold.*` en prod; no es un 500).
- `/api/v1/agente/consulta` → **200 degradado seguro** (`sql_generado:null`, `fuera_de_alcance:false`):
  no es el stub, pero el RAG real sigue pendiente de C3.

## Estado de las historias de C5 al cierre de S4

- **US-501 / US-502 / US-504 / US-505** — entregadas y mergeadas. La parte de C5 (Luis) de REQ-005
  para Fases 0/1/2 está **cerrada**.
- **REQ-005 en su conjunto sigue 🟡** porque incluye historias de otros miembros de C5 aún abiertas
  (US-522a/b/c Airflow, US-524a/b/c monitoreo, US-525a/b/c) → PRs #87 y #102.

## Retro C5 — dependencias vivas (insumo para el PO)

Puntos donde **el equipo depende hoy de C5/Luis** para avanzar (candidatos de S5):

- **DEP-1 · Deploy 100% manual (bus-factor).** Toda release a prod depende de mi disponibilidad;
  no hay CD. Mitigación: `deploy.yml` + runbook de deploy/restore (Fase 4, requiere revisión CI/CD).
- **DEP-2 · Ecosistema en prod (Fase 3, gated).** Hoy solo vive el API. C2 (Superset) y C3
  (MLflow/ChromaDB/agente RAG) no tienen superficie pública para la demo hasta que se despliegue
  el ecosistema + IAP. Es la dependencia de mayor peso de cara al 9-sep. **Requiere "go" + costo (~$170/mo).**
- **DEP-3 · Credenciales OAuth de Google (gated).** C4·Christian no puede validar `RealGoogleVerifier`
  e2e sin el `client_id`/`client_secret`, que solo yo creo en consola. Bloquea el flip
  `AUTH_LECTURA_PUBLICA=false`.
- **DEP-4 · Deploy final del agente.** Cuando C3 entregue `generar_sql`/`redactar_respuesta` (LLM),
  C5 debe añadir `chromadb`/`sentence-transformers` a `docker/api.Dockerfile` y redimensionar imagen/memoria.
  Adelantable: dejar el Dockerfile listo sin desplegar.
- **DEP-5 · PRs de C5 atorados.** #87 (US-522b Airflow, CONFLICTING + CI en rojo + **colisión de ID
  ADR-007** → renombrar a ADR-008 + quitar fixture binario) y #102 (US-524a, CONFLICTING) esperan mi
  revisión como Tech Lead.

## Bloqueantes / avisos a otros owners

- **Edgar (PO, owner de `06_Quality_Testing/Bug_Register.md`):** BUG-020 está **curado en prod** y
  BUG-025 **parcialmente resuelto y desplegado**; el registro aún los marca `open`. El PR #149
  reconcilia el vault post-ADR-007 (MERGEABLE, 4/4 CI verde) → recomiendo mergearlo para que el
  tablero PM deje de sobreestimar el riesgo antes de la demo.
- **Andrés (C3):** el agente en prod degrada seguro pero necesita el LLM real (`generar_sql`/
  `redactar_respuesta`) para cerrar BUG-025 al 100%.
- **Christian (C4):** el flip a lectura cerrada depende de `RealGoogleVerifier` + `state` CSRF
  aleatorio; la parte C5 (credenciales OAuth) queda lista para entregarte en cuanto Luis dé el "go".

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos:** este DevLog, `_DevLog/_index.md`, `02_Requirements/Traceability_Matrix.md`.
- **Sin cambios de código ni de infraestructura GCP.** Solo lectura de prod (curl a la URL pública)
  para dejar evidencia de validación fechada. `vault_lint.py` verde; diff sin secretos.
