---
id: AGENTCTX-ELOISA-GONZALEZ
title: "Agent Context — Eloisa González Rubio"
owner: "Eloisa González Rubio"
status: approved
traces_up: ["vault/12_Roadmap_Sprints/Sprints/4-eloisa-gonzalez-rubio"]
tags: [ai, agent-context, ownership, celula-4]
---

# Agent Context — Eloisa González Rubio

> El agente IA de esta persona **debe leer este archivo al inicio de cada sesión**.
> Define qué puede tocar. Si va a modificar un archivo 🔴, **debe detenerse y avisar**.
> → [[vault/09_AI_Governance/AI_Agent_Governance]] · Plan: [[vault/12_Roadmap_Sprints/Sprints/4-eloisa-gonzalez-rubio]]

---

## 1. Identificación

| | |
|---|---|
| **Nombre** | Eloisa González Rubio |
| **Identidad** | `eloisa-gonzalez` |
| **Rama fija** | `dev/eloisa-gonzalez` — permanente, no se borra al mergear |
| **Célula** | Celula 4 — Backend, API & Seguridad |
| **Nivel** | Bajo |
| **Rol** | Desarrolladora jr · Pruebas de API |
| **Tech Lead de la célula** | Christian Imanol Ruiz Hurtado |
| **Quién revisa su código** | Edgar Edmundo Coronel Navarrete (PM) — compuerta única (DEC-003). Christian Imanol Ruiz Hurtado (Tech Lead) revisa como apoyo, no bloquea |
| **Requisito(s) que cubre** | REQ-004 (Backend, API y autenticación avanzada) |

---

## 2. 🟢 Alcance permitido (crear y modificar con IA libremente)

- `src/api/**`
- `vault/03_Architecture/API_Specification.md`
- Su propio plan de sprint y su DevLog en `vault/_DevLog/`.

> Definido en `vault/_Meta/ownership.yml`, que es lo que el CI verifica en cada PR.
> Si esta lista y ese archivo no coinciden, **manda el archivo**.

---

## 3. 🟡 Compartidos (coordinar con el dueño antes de tocar)

| Archivo / artefacto | Dueño | Protocolo |
|---|---|---|
| `tests/**` | dueño del área | cambio acotado; avisar en el PR |
| Endpoints de datos sobre Gold | Diana Alvarez (C1) | depende del esquema de Gold |
| Endpoints de inferencia ML | Andrés González Habib (C3) | depende del contrato de modelos |
| Módulo de auth del frontend | Manuel Serranía (C2) | exponer login/roles para vistas protegidas |
| `vault/02_Requirements/Traceability_Matrix.md` | PM — Edgar Coronel | actualiza su fila; el PM consolida |
| `_index.md` de las carpetas que toca | PM / dueño de carpeta | registrar cada artefacto nuevo |

---

## 4. 🔴 Fuera de alcance (nunca tocar con IA sin autorización)

| Ruta / área | Dueño | A quién pedir |
|---|---|---|
| `src/ingesta/**`, `dbt/**`, `dags/**` | C1 — Diana Alvarez | pedir a Data Eng |
| `src/modelos/**` | C3 — Andrés González Habib | pedir a ML |
| `superset/**` | C2 — Manuel Serranía | pedir a BI |
| `.github/**` | C5 — Luis Téllez | pedir a DevOps |
| `vault/_Meta/**` | PM — Edgar Coronel | pedir al PO |

> **Regla 7 del vault:** todo cambio de **esquema, seguridad o CI/CD** requiere **revisión
> humana explícita** antes de mergear.

---

## 5. Historias asignadas

| ID | Sprint | Objetivo |
|---|---|---|
| US-421 | S3 | Estructura del proyecto, `/health`, configuracion por variables de entorno y documentacion automatica. |
| US-422 | S4 | pytest + httpx sobre los endpoints; cobertura minima segun Definition_of_Done. |
| US-423 | S5 | Expiracion de token, acceso denegado por rol, rutas protegidas. Hallazgos como SEC-###. |

---

## 6. Reglas de uso de IA que aplican

- **DevLog obligatorio por sesión con IA**, antes del push (`vault/_DevLog/YYYY-MM-DD-eloisa-gonzalez-*.md`).
- **Revisión línea por línea** de todo código generado por IA: es responsable de lo que sube.
- **Prohibido pegar en un prompt**: `.env`, datos reales, credenciales o tokens.
- **Nunca commit directo a `main`**: todo entra por PR desde su rama fija `dev/eloisa-gonzalez`.
- **Una sola rama, permanente.** No se abre otra por historia, sprint ni tema; no se borra
  al mergear. Se sincroniza con `git merge origin/main` antes de trabajar y antes del PR.
- **Nunca `rebase` ni `--force`** sobre `dev/eloisa-gonzalez`.
- Commits en Conventional Commits con el ID de la historia.
- No trabajar fuera de este alcance: el CI reprueba el PR que toca archivos ajenos.
  Para cambiar algo de otra persona, pedírselo a su dueño y que lo lleve en su rama.

---

## 7. Contexto técnico específico

- **FastAPI** con validación de entradas por **Pydantic**; no filtrar detalles internos en los errores.
- **OAuth2 + JWT** (access + refresh tokens). **RBAC de 2 roles**: ciudadano/estándar vs analista/admin.
- Contrato **OpenAPI** publicado en Semana 1 para desacoplar a C2 y C3 (trabajan contra mocks).
- Consume Gold (C1) y modelos (C3); no reimplementa lógica de datos ni de ML.

---

## 8. Prompts iniciales sugeridos (agnósticos de LLM)

> Funcionan en Claude Code, ChatGPT, Gemini o Copilot. Todo lo generado se revisa antes de
> commitear, y cada sesión genera DevLog.

**Contexto para pegar al inicio de la sesión:**
```
Soy de Backend, API & Seguridad en FASTAPI para FARO. OAuth2/JWT con refresh/access tokens, RBAC de 2 roles, validacion Pydantic, contrato OpenAPI. Responde en espanol con codigo comentado.
```

**FastAPI:**
```
Implementa el endpoint <ruta> en FastAPI con validacion Pydantic y manejo de errores que no filtre trazas internas. Documenta en OpenAPI.
```

**OAuth2/JWT:**
```
Implementa OAuth2 con JWT (access + refresh) y renovacion de token. Explica el flujo y el manejo seguro de los tokens.
```

**RBAC:**
```
Implementa RBAC con 2 roles (ciudadano y analista/admin) y protege un endpoint segun rol. Escribe pruebas de 401/403/200.
```
