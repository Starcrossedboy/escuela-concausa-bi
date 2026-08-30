---
project: "FARO"
date: "2026-08-29"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1h"
touches: ["US-505", "REQ-005", "BUG-020", "DEC-9"]
tags: [devlog, cloud, devops, security, gcp, cloud-run, cloud-sql]
---

# DevLog — 2026-08-29 — US-505: Fase 2 — poblar Gold en Cloud SQL + redeploy del API (BUG-020 en prod)

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

**Fase 2 del plan de Célula 5: se curó BUG-020 en PRODUCCIÓN.** Con la base privada
ya aprovisionada en Fase 1 (US-504), se pobló Gold en Cloud SQL y se redesplegó el
API en Cloud Run conectado a la DB por la red privada. `/api/v1/escuelas` pasa de
**500** a **200 con 25 escuelas reales**.

### 1. Poblar Gold en Cloud SQL (`faro`)

Se reusó la vía documentada por Diana (fixtures Bronze + `dbt run` acotado) que ya
había curado BUG-020 end-to-end en local, ahora contra Cloud SQL:

- Como `faro-postgres` **no tiene IP pública** (IP privada `172.21.0.3`, por diseño),
  no es alcanzable desde fuera de la VPC. Se resolvió con una **IP pública temporal**
  (`--assign-ip`) + **Cloud SQL Auth Proxy corrido como contenedor oficial de Google**
  (`gcr.io/cloud-sql-connectors/cloud-sql-proxy`) autenticado con un **token OAuth
  efímero** de la sesión `gcloud` (sin descargar binarios sueltos, sin abrir
  `authorized-networks`, sin llaves de SA). La contraseña `faro_app` se leyó de
  Secret Manager a una variable de entorno **sin imprimirse jamás**.
- Bootstrap en contenedor `python:3.11`: 10 fixtures Bronze (idempotente) →
  `dbt run --select +dim_escuela +dim_municipio +dim_tiempo +fact_escuela_ciclo
  +features_escuela +matricula_municipio_nivel --exclude agua_region` (**PASS=14**) →
  stubs vacíos `gold.predicciones` / `gold.recomendaciones` (runtime sources de ML).
- Conteos idénticos al local y a los de Diana: **60/10/2/25/25/72**
  (`dim_escuela`/`dim_municipio`/`dim_tiempo`/`fact_escuela_ciclo`/`features_escuela`/
  `matricula_municipio_nivel`); `predicciones`/`recomendaciones` = 0 (esperado).
- **Cerrada la exposición inmediatamente:** proxy detenido y `--no-assign-ip`
  → la instancia vuelve a quedar **solo con IP privada**. Ventana pública ~1 min.

### 2. Redeploy del API a Cloud Run (misma imagen, config segura)

Se actualizó `08_CICD_DevOps/scripts/deploy-cloud-run.sh` y se redesplegó la **misma
imagen** que ya corría (`faro-api:v0.2.1-hotfix-bug008`, sin rebuild) con:

- `--service-account=faro-api-sa` → deja de correr con la **SA por defecto de Compute**
  (sobre-privilegiada) y pasa a la de **mínimo privilegio** de Fase 1.
- `--vpc-connector=faro-connector --vpc-egress=private-ranges-only` → alcanza Cloud SQL
  por **IP privada** sin exponer la DB.
- `--set-secrets=JWT_SECRET_KEY=jwt-secret-key:latest,POSTGRES_PASSWORD=db-password:latest`
  → **cierra la violación de `Secrets_Policy.md`**: `JWT_SECRET_KEY` ya **no** viaja como
  env var en texto plano; ambos secretos se inyectan en runtime desde Secret Manager.
- `--set-env-vars` de conexión no sensible: `ENVIRONMENT=production`,
  `POSTGRES_HOST=172.21.0.3`, `POSTGRES_PORT=5432`, `POSTGRES_DB=faro`,
  `POSTGRES_USER=faro_app`.
- Se mantiene `--allow-unauthenticated` (la rúbrica exige URL pública viva del API;
  las UIs admin NO son públicas → van tras IAP en Fase 3).

Revisión desplegada: `faro-api-00005-qc8` (100% del tráfico).

### 3. Verificación en producción

- `GET /api/v1/health` → **200** `{"status":"ok"}`.
- `GET /api/v1/escuelas` → **200**, `total=25` escuelas reales (CDMX/Edomex),
  `tiene_prediccion:false` (correcto, stubs ML vacíos).
- `GET /api/v1/predicciones/{cct}` → **404 estructurado** (no 500): la DB conecta y el
  endpoint consulta `gold.predicciones` vacía → comportamiento esperado hasta que ML
  publique (Fase 3). Confirmado en `gcloud run services describe`: SA, connector,
  egress y ambos `secretKeyRef` presentes.

**BUG-020 queda CURADO en prod** (estaba curado en local desde Fase 0). URL pública viva
sirviendo datos reales → mitiga RISK-001 (nota tope 6.0 sin URL viva).

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code / claude-opus-4-8
- **Archivos creados/modificados:**
  - `08_CICD_DevOps/scripts/deploy-cloud-run.sh` (modificado: SA + connector + secrets + DB env)
  - `08_CICD_DevOps/Cloud_Run_Deploy.md` (nueva sección §4.3 deploy productivo Fase 2)
  - `_DevLog/2026-08-29-luis-tellez-us505-fase2-gold-cloudsql-redeploy.md` (este)
  - `_DevLog/_index.md` (fila)
  - `02_Requirements/Traceability_Matrix.md` (evidencia US-505 en REQ-005)
  - `_local/bootstrap_gold_cloudsql.sh` (NO versionado; `_local/` está en `.gitignore`)
- **Decisiones autónomas del agente:** P-6 = poblar Gold vía IP pública **temporal** +
  Cloud SQL Auth Proxy en contenedor con token OAuth efímero (elegido por Luis entre las
  opciones presentadas); redeploy de la **misma imagen** (no rebuild) porque `config.py`
  ya lee `POSTGRES_*`; `--vpc-egress=private-ranges-only` (solo RFC1918 por el connector);
  **no** inyectar `fernet-key` (el API no lo usa en runtime → mínimo privilegio).
- **Correcciones manuales:** —
- **Prompt inicial:** "A->B" (go explícito de Luis para Fase 2, tras aprobar el detalle).

## Seguridad / calidad
- [x] Sin secretos hardcodeados (token OAuth y `db-password` nunca impresos; JWT y DB
      pasan a Secret Manager en runtime → se cierra V2/V4 y la violación de texto plano)
- [x] Exposición pública de la DB minimizada (IP pública solo ~1 min, sin authorized-networks)
- [ ] Tests agregados/actualizados (deploy de infra; la guarda funcional es el propio
      `GET /api/v1/escuelas` → 200 verificado en prod)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- Ninguno para Fase 2. `/predicciones` y `/recomendaciones` devuelven vacío/404 hasta que
  ML-01/02 publiquen a `gold.*` (Fase 3, Célula 3).

## Próximos pasos
1. **Fase 3:** desplegar el ecosistema (Airflow/MLflow/Superset/ChromaDB) + **IAP** para
   las UIs admin (no públicas). ML publica predicciones → `/predicciones` deja de ser 404.
2. **Fase 4:** Load Balancer HTTPS + Cloud Armor (Escenario B), CD `deploy.yml`,
   prueba de restore de backups.
