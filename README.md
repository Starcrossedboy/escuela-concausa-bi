# FARO — Project Vault (SDLC-with-AI Standard)

> Vault estándar para gestionar **todo el ciclo de vida de desarrollo de software asistido por IA**,
> con trazabilidad total entre requerimientos, código, pruebas, seguridad y releases.
>
> **Cómo empezar:** abre [[00_Start_Here/PROJECT_INDEX]].

---

## Qué es este vault

Un sistema de documentación viva (compatible con Obsidian y con cualquier editor Markdown) que
garantiza que **nada quede huérfano**: cada requisito, decisión, bug, hallazgo de seguridad y
sesión de IA tiene un **ID**, un **dueño**, un **lugar** y **enlaces** hacia lo que lo origina y
lo que lo implementa.

Está diseñado para equipos que trabajan con agentes de IA (Claude Code, Codex, Gemini, etc.) y
necesitan **auditar qué hizo la IA**, **cumplir un PRD** y **pasar quality gates** antes de release.

## Principios (ver [[_Meta/Vault_Rules]])

1. **Todo tiene ID y dueño** — `REQ-`, `US-`, `ADR-`, `RISK-`, `SEC-`, `TEST-`, `BUG-`, `TASK-`.
2. **Una sola fuente de verdad por tema** — sin copias duplicadas.
3. **Trazabilidad bidireccional** — `traces_up` / `traces_down` en el frontmatter.
4. **Definition of Filed** — nada está "reportado" hasta tener ID + carpeta + enlace + índice actualizado.
5. **Enforcement > convención** — las reglas se vuelven CI, plantillas de PR y branch protection.

## Mapa del ciclo de vida

| Fase | Carpeta |
|---|---|
| Producto / visión | `01_Product` |
| Requerimientos (general + detallado) + **trazabilidad** | `02_Requirements` |
| Arquitectura + decisiones (ADR) | `03_Architecture` |
| UX / Diseño | `04_UX_Design` |
| Ingeniería (git, DoD, PR, estándares) | `05_Engineering` |
| **Pruebas** (automáticas + físicas/manuales) | `06_Quality_Testing` |
| **Ciberseguridad** | `07_Security` |
| CI/CD & DevOps | `08_CICD_DevOps` |
| **Gobernanza de IA** | `09_AI_Governance` |
| Riesgos / decisiones / incidentes | `10_Risk_Governance` |
| Operación / runbooks / SLOs | `11_Operations` |
| Roadmap & Sprints | `12_Roadmap_Sprints` |
| Reportes ejecutivos & auditorías | `13_Reports` |

Carpetas de soporte: `_Templates` (plantillas), `_DevLog` (bitácora única), `_Meta` (reglas del vault).

## 🚀 Despliegue

### URL de Producción

**API Principal:** [https://faro-api-eanzfglvyq-uc.a.run.app](https://faro-api-eanzfglvyq-uc.a.run.app)

**Endpoints disponibles** (todos bajo el prefijo `/api/v1/`):
- `GET /api/v1/health` — Health check
- `GET /api/v1/version` — Versión de la API (`api`, `commit`)
- `GET /api/v1/kpis` — KPIs del tablero
- `GET /api/v1/escuelas` · `GET /api/v1/escuelas/{cct}` — Escuelas
- `GET /api/v1/municipios` · `GET /api/v1/municipios/{cve_mun}` — Municipios
- `GET /api/v1/predicciones/{cct}` — Predicción de matrícula de una escuela
- `GET /api/v1/docs` — Documentación interactiva (Swagger UI) con el catálogo completo

**Infraestructura:**
- Platform: Google Cloud Run
- Región: us-central1 (Iowa, USA)
- Proyecto: faro-escuela-sensor
- Organización: luis-g-roses-org
- Límite de instancias: 1 (ambiente de prueba)

**Deploy manual:**
```bash
# Build y push
./08_CICD_DevOps/scripts/build-and-push.sh v0.1.0-s1

# Deploy a Cloud Run
./08_CICD_DevOps/scripts/deploy-cloud-run.sh v0.1.0-s1
```

Ver procedimiento completo: [[08_CICD_DevOps/Cloud_Run_Deploy]]

---

## Cómo adoptar este vault en tu proyecto

Ver [[_Meta/Adoption_Guide]] — reemplaza los placeholders `{{...}}`, asigna dueños y crea tu primer PRD.

---

**Placeholders a reemplazar globalmente:** `FARO`, `Edgar Edmundo Coronel Navarrete`, `https://github.com/edgarcoroneln/escuela-concausa-bi`,
`Python 3.11 · Airflow · dbt · Postgres · Superset · MLflow · FastAPI · Docker · GCP`, `2026-08-01`, `Edgar Edmundo Coronel Navarrete`.
