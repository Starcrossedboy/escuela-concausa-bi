---
id: AGENTCTX-EDWARD-RUIZ
title: "Agent Context — Edward Ulysses Ruiz Bustillos"
owner: "Edward Ulysses Ruiz Bustillos"
status: approved
traces_up: ["vault/12_Roadmap_Sprints/Sprints/5-edward-ulysses-ruiz-bustillos"]
tags: [ai, agent-context, ownership, celula-5]
---

# Agent Context — Edward Ulysses Ruiz Bustillos

> El agente IA de esta persona **debe leer este archivo al inicio de cada sesión**.
> Define qué puede tocar. Si va a modificar un archivo 🔴, **debe detenerse y avisar**.
> → [[vault/09_AI_Governance/AI_Agent_Governance]] · Plan: [[vault/12_Roadmap_Sprints/Sprints/5-edward-ulysses-ruiz-bustillos]]

---

## 1. Identificación

| | |
|---|---|
| **Nombre** | Edward Ulysses Ruiz Bustillos |
| **Identidad** | `edward-ruiz` |
| **Rama fija** | `dev/edward-ruiz` — permanente, no se borra al mergear |
| **Célula** | Celula 5 — Cloud Infrastructure & DevOps |
| **Nivel** | Bajo |
| **Rol** | DevOps jr · Monitoreo y documentacion |
| **Tech Lead de la célula** | Luis Téllez Domínguez |
| **Quién revisa su código** | Edgar Edmundo Coronel Navarrete (PM) — compuerta única (DEC-003). Luis Téllez Domínguez (Tech Lead) revisa como apoyo, no bloquea |
| **Requisito(s) que cubre** | REQ-005 (despliegue GCP) y REQ-007 (CI/gobernanza) |

---

## 2. 🟢 Alcance permitido (crear y modificar con IA libremente)

- `.github/**` (CI/CD)
- `docker/**`
- `docker-compose.yml`
- `infra/**`
- `vault/08_CICD_DevOps/**`
- `vault/11_Operations/**`
- Su propio plan de sprint y su DevLog en `vault/_DevLog/`.

> Definido en `vault/_Meta/ownership.yml`, que es lo que el CI verifica en cada PR.
> Si esta lista y ese archivo no coinciden, **manda el archivo**.

---

## 3. 🟡 Compartidos (coordinar con el dueño antes de tocar)

| Archivo / artefacto | Dueño | Protocolo |
|---|---|---|
| `requirements/**` | dueño del área | cambio acotado; avisar en el PR |
| `scripts/**` | dueño del área | cambio acotado; avisar en el PR |
| `tests/**` | dueño del área | cambio acotado; avisar en el PR |
| Esquema Postgres / Cloud SQL | Diana Alvarez (C1) | coordinar migraciones |
| Secretos y variables (`vault/07_Security`) | Christian Ruiz (C4) | gestor de secretos, nunca en el repo |
| Imágenes de cada servicio | dueño del código de cada célula | acordar Dockerfile por servicio |
| `vault/02_Requirements/Traceability_Matrix.md` | PM — Edgar Coronel | actualiza su fila; el PM consolida |
| `_index.md` de las carpetas que toca | PM / dueño de carpeta | registrar cada artefacto nuevo |

---

## 4. 🔴 Fuera de alcance (nunca tocar con IA sin autorización)

| Ruta / área | Dueño | A quién pedir |
|---|---|---|
| `src/api/**` | C4 — Christian Ruiz | pedir a Backend |
| `src/modelos/**` | C3 — Andrés González Habib | pedir a ML |
| `src/ingesta/**`, `dbt/**` | C1 — Diana Alvarez | pedir a Data Eng |
| `superset/**` | C2 — Manuel Serranía | pedir a BI |
| `vault/_Meta/**` | PM — Edgar Coronel | pedir al PO |

> **Regla 7 del vault:** todo cambio de **esquema, seguridad o CI/CD** requiere **revisión
> humana explícita** antes de mergear.

---

## 5. Historias asignadas

| ID | Sprint | Objetivo |
|---|---|---|
| US-521c | S1 | Documentar el setup local de Superset y el agente (RAG/ChromaDB): variables, puertos y verificacion. |
| US-522c | S3 | Dockerfile y servicios en docker-compose para Superset y el agente (RAG/ChromaDB), con healthchecks. |
| US-523c | S3 | Configurar el gate que corre `vault_lint.py` y verifica la plantilla de PR completa. |
| US-524c | S5 | Metricas, logs y alertas para Superset y el agente. |
| US-525c | S6 | Procedimiento probado de rollback para Superset y el agente. |

---

## 6. Reglas de uso de IA que aplican

- **DevLog obligatorio por sesión con IA**, antes del push (`vault/_DevLog/YYYY-MM-DD-edward-ruiz-*.md`).
- **Revisión línea por línea** de todo código generado por IA: es responsable de lo que sube.
- **Prohibido pegar en un prompt**: `.env`, datos reales, credenciales o tokens.
- **Nunca commit directo a `main`**: todo entra por PR desde su rama fija `dev/edward-ruiz`.
- **Una sola rama, permanente.** No se abre otra por historia, sprint ni tema; no se borra
  al mergear. Se sincroniza con `git merge origin/main` antes de trabajar y antes del PR.
- **Nunca `rebase` ni `--force`** sobre `dev/edward-ruiz`.
- Commits en Conventional Commits con el ID de la historia.
- No trabajar fuera de este alcance: el CI reprueba el PR que toca archivos ajenos.
  Para cambiar algo de otra persona, pedírselo a su dueño y que lo lleve en su rama.

---

## 7. Contexto técnico específico

- Despliegue en **GCP**: Cloud Run + Cloud SQL + Artifact Registry. Todo **dockerizado**.
- **URL pública viva** es obligatoria (sin ella, techo 6.0). Deploy 'hola mundo' en Semana 1.
- Servicios del ecosistema: FastAPI, agente, jobs de ML, Airflow, Superset, Postgres.
- Secretos fuera del repo (gestor de secretos). CI en GitHub Actions: lint + pruebas + `vault_lint.py`.

---

## 8. Prompts iniciales sugeridos (agnósticos de LLM)

> Funcionan en Claude Code, ChatGPT, Gemini o Copilot. Todo lo generado se revisa antes de
> commitear, y cada sesión genera DevLog.

**Contexto para pegar al inicio de la sesión:**
```
Soy de Cloud & DevOps en FARO. Todo dockerizado en GCP (Cloud Run + Cloud SQL + Artifact Registry), CI en GitHub Actions, URL publica viva. Responde en espanol con codigo comentado.
```

**Dockerfile:**
```
Escribe el Dockerfile y el servicio de docker-compose para <servicio>, con healthcheck y sin secretos hardcodeados.
```

**Cloud Run:**
```
Dame los pasos para desplegar <servicio> en GCP Cloud Run con Artifact Registry y Cloud SQL, exponiendo una URL publica estable.
```

**CI GitHub Actions:**
```
Escribe el workflow de CI que corra lint, pytest y vault_lint.py y bloquee el merge si algo falla.
```
