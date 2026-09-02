---
project: "FARO"
date: "2026-08-29"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "4h"
touches: ["US-502", "REQ-005", "BUG-020", "META-RULES"]
tags: [devlog, celula-5, docker, compose, worktrees, e2e]
---

# DevLog — 2026-08-29 — US-502: docker-compose sin `container_name` + validación E2E local

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/06_Quality_Testing/Bug_Register]]

## Contexto

El stack de US-502 (`docker-compose.yml`) fijaba el nombre de cada contenedor con
`container_name: faro-*`. Los nombres de contenedor son **globales en Docker**, así que
levantar el mismo stack desde un `git worktree` y desde la copia principal del repo
colisiona (`Conflict. The container name "/faro-postgres" is already in use`). Esto
bloqueaba correr el ecosistema en paralelo y ensuciaba el estado compartido.

Esta sesión forma parte del curado **local** de **BUG-020** (rutas de datos/ML en 500):
antes de tocar GCP se decidió (DEC-4) validar el ecosistema completo en local.

## Qué se hizo

### 1. `docker-compose.yml` — eliminar `container_name` fijos
- Removidas las 8 líneas `container_name: faro-*`. Sin ellas, Compose nombra los
  contenedores `<proyecto>-<servicio>-<N>` (proyecto = nombre de carpeta), permitiendo
  que varias copias coexistan. Se documentó la regla en un comentario del archivo:
  **referirse siempre a los servicios por su nombre de servicio** (`db`, `api`, `mlflow`…).
- **Healthcheck de `chromadb` reescrito.** La imagen `chromadb/chroma:latest` no trae
  `curl`/`wget`/`python` (`exec: "curl": not found` → falso `unhealthy` aunque el servicio
  responde). Se usa `bash` con `/dev/tcp` para hablar HTTP al `/api/v2/heartbeat` sin
  dependencias externas.

### 2. Scripts de verificación agnósticos al proyecto
- `scripts/verify-docker-compose.sh`: resuelve el contenedor vía `docker compose ps -q
  <servicio>` en vez de un nombre fijo; hace `cd` a la raíz del repo; se quitó `set -e`
  a propósito (el script corre TODAS las verificaciones y resume con `ALL_OK`). Además
  dos correcciones de **falsos negativos**: (a) Postgres se verifica con `check_port` (no
  `check_http`, que envenenaba `ALL_OK` contra un puerto no-HTTP); (b) la ruta de salud
  del API es `/api/v1/health` (200), no `/health` (404).
- `scripts/verificar-servicios.sh`: `docker compose exec -T db …` en vez de
  `docker exec faro-postgres …`; `cd` a la raíz del repo.

### 3. `.gitignore` — notas de trabajo locales
- Se ignora `_local/` (documentos de referencia/handoff personales por sprint, no
  versionables; sirven para retomar contexto entre sesiones de IA).

### 4. `vault_lint.py` — excluir `_local/`
- `_local/` agregado a `EXCLUDED_DIRS`, consistente con `.venv`/`node_modules`
  (directorios gitignored que no son artefactos del vault). Sin esto, el lint daba rojo
  en local por un archivo personal sin frontmatter; en CI/checkout limpio ya daba verde
  (verificado con `git archive HEAD`). Toca [[vault/_Meta/Naming_Conventions|META-RULES]].

### 5. Validación E2E local (curado de BUG-020 en LOCAL)
- Volumen `faro-postgres-data` recreado limpio (curó `password authentication failed`).
- Gold poblado con contenedor `python:3.11` efímero: fixtures Bronze + `dbt run` acotado
  (`--exclude agua_region` por BUG-009) + stubs vacíos `gold.predicciones`/`recomendaciones`
  (son *runtime sources* de ML, deben existir aunque vacías o el JOIN de `/escuelas` truena).
  Conteos: **60/10/2/25/25/72** (idénticos a los de Diana Alvarez).
- **8 servicios arriba y verificados verdes** (arranque incremental para evitar OOM;
  `mlflow` ~2.16 GiB el más pesado; total ~4.0/7.7 GiB). `verify-docker-compose.sh` →
  "🎉 TODOS LOS SERVICIOS ESTÁN FUNCIONANDO CORRECTAMENTE".
- `/api/v1/escuelas` → **HTTP 200 con 25 escuelas reales** (CDMX/Edomex),
  `tiene_prediccion:false` (correcto, stubs ML vacíos). **BUG-020 curado end-to-end en LOCAL.**

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos creados/modificados (repo):** `docker-compose.yml`,
  `scripts/verify-docker-compose.sh`, `scripts/verificar-servicios.sh`, `.gitignore`,
  `vault/_Meta/scripts/vault_lint.py`; este DevLog + `vault/_DevLog/_index.md` +
  `vault/02_Requirements/Traceability_Matrix.md`.
- **Decisiones autónomas del agente:** diagnóstico de los 3 falsos negativos de
  verificación (healthcheck de chromadb, Postgres no-HTTP, ruta de salud del API);
  simulación del lint sobre `git archive HEAD` para probar que el rojo era solo local.
- **Correcciones manuales:** Luis aprobó Escenario B, P-1=opción A y P-4=opción A2; pidió
  validar el cumplimiento de reglas ANTES de commit/PR.
- **Prompt inicial:** retomar el plan `_local/plan_Luis_S4.md` (Fase 0).

## Seguridad / calidad
- [x] Sin secretos hardcodeados (`.env` gitignored y no trackeado; diff sin credenciales)
- [x] Verificación E2E ejecutada (`verify-docker-compose.sh` verde; `/api/v1/escuelas` 200)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- **BUG-020 en PRODUCCIÓN sigue abierto:** Cloud Run no tiene DB (cae a `localhost:5432`);
  Cloud SQL Admin API deshabilitada. Se cura en Fase 2 (GCP), **gated** por autorización de Luis.
- **GCP gated (P-3):** no ejecutar Fase 1+ sin "go" explícito.

## Próximos pasos
- Abrir PR de la rama `feat/luis-tellez-compose-sin-container-name` al PM.
- Workstream documental de seguridad (CIS 5.3, `Security_Model.md`, US IDs en
  `Threat_Model.md`, `Compliance.md`, `generate-keys.py`) — sin GCP.
- Fase 1 GCP tras "go".
