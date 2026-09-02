---
id: AGENTCTX-DIANA-ALVAREZ
title: "Agent Context — Diana Aracely Alvarez Varela"
owner: "Diana Aracely Alvarez Varela"
status: approved
traces_up: ["vault/12_Roadmap_Sprints/Sprints/1-diana-aracely-alvarez-varela"]
tags: [ai, agent-context, ownership, celula-1]
---

# Agent Context — Diana Aracely Alvarez Varela

> El agente IA de esta persona **debe leer este archivo al inicio de cada sesión**.
> Define qué puede tocar. Si va a modificar un archivo 🔴, **debe detenerse y avisar**.
> → [[vault/09_AI_Governance/AI_Agent_Governance]] · Plan: [[vault/12_Roadmap_Sprints/Sprints/1-diana-aracely-alvarez-varela]]

---

## 1. Identificación

| | |
|---|---|
| **Nombre** | Diana Aracely Alvarez Varela |
| **Identidad** | `diana-alvarez` |
| **Rama fija** | `dev/diana-alvarez` — permanente, no se borra al mergear |
| **Célula** | Celula 1 — Data Engineering & Quality |
| **Nivel** | Alto |
| **Rol** | Tech Lead · Data Engineering |
| **Tech Lead de la célula** | Diana Aracely Alvarez Varela |
| **Quién revisa su código** | Edgar Edmundo Coronel Navarrete (PM) — compuerta única (DEC-003). Diana Aracely Alvarez Varela (Tech Lead) revisa como apoyo, no bloquea |
| **Requisito(s) que cubre** | REQ-001 (Data Engineering y pipelines multi-fuente) |

---

## 2. 🟢 Alcance permitido (crear y modificar con IA libremente)

- `src/ingesta/**`
- `dbt/**`
- `dags/**`
- `vault/14_Data_Sources/**`
- `vault/03_Architecture/Data_Model.md`
- Su propio plan de sprint y su DevLog en `vault/_DevLog/`.

> Definido en `vault/_Meta/ownership.yml`, que es lo que el CI verifica en cada PR.
> Si esta lista y ese archivo no coinciden, **manda el archivo**.

---

## 3. 🟡 Compartidos (coordinar con el dueño antes de tocar)

| Archivo / artefacto | Dueño | Protocolo |
|---|---|---|
| `tests/**` | dueño del área | cambio acotado; avisar en el PR |
| `great_expectations/**` | dueño del área | cambio acotado; avisar en el PR |
| `requirements/celula-1.txt` | dueño del área | cambio acotado; avisar en el PR |
| `gold.features_escuela` (contrato de features) | Andrés González Habib (C3) | avisar antes de cambiar columnas (US-104) |
| Cubos de Gold para BI | Manuel Serranía (C2) | avisar cambios de grano/métricas |
| Endpoints de datos sobre Gold | Christian Ruiz (C4) | avisar cambios de esquema |
| Esquema Postgres / Cloud SQL | Luis Téllez (C5) | coordinar cambios de esquema (infra) |
| `vault/02_Requirements/Traceability_Matrix.md` | PM — Edgar Coronel | actualiza su fila; el PM consolida |
| `_index.md` de las carpetas que toca | PM / dueño de carpeta | registrar cada artefacto nuevo |

---

## 4. 🔴 Fuera de alcance (nunca tocar con IA sin autorización)

| Ruta / área | Dueño | A quién pedir |
|---|---|---|
| `src/api/**` | C4 — Christian Ruiz | pedir a Backend |
| `src/modelos/**` | C3 — Andrés González Habib | pedir a ML |
| `superset/**` | C2 — Manuel Serranía | pedir a BI |
| `.github/**` (CI/CD) | C5 — Luis Téllez | pedir a DevOps |
| `vault/_Meta/**` | PM — Edgar Coronel | pedir al PO |
| `vault/07_Security/**` | C4 — Christian Ruiz | pedir a Seguridad |

> **Regla 7 del vault:** todo cambio de **esquema, seguridad o CI/CD** requiere **revisión
> humana explícita** antes de mergear.

---

## 5. Historias asignadas

| ID | Sprint | Objetivo |
|---|---|---|
| US-101 | S1 | Contrato de las 3 capas: Bronze (raw + metadatos), Silver (tipado, CCT homologado) y Gold (esquema estrella). Incluye el parametro `SCOPE_ENTIDADES` y la politica de cobertura parcial. Documentar en `vault/03_Architecture/Data_Model.md`. |
| US-102 | S2 | DAG con dependencias, reintentos, alertas y particionado por fecha. Debe manejar 8 fuentes con periodicidad distinta: horaria, diaria, mensual, anual y censal. |
| US-103 | S3 | `fact_escuela_ciclo` + dim_escuela, dim_municipio, dim_tiempo, dim_driver. Es la pieza de mayor peso en la rubrica: debe quedar impecable. |
| US-104 | S3 | `gold.features_escuela`: los 6 drivers normalizados + banderas de cobertura. Contrato cerrado y versionado con la Celula 3. |
| US-105 | S3 | Interpolacion IDW para SINAICA dentro de radio valido; fuera de radio, marcar `SIN_DATO` explicito (nunca cero ni nulo silencioso). Calcular `indice_completitud_drivers` por escuela. |
| US-106 | S5 | Diagrama fuente->bronze->silver->gold->feature->modelo->dashboard. Freeze el 6 de septiembre. |

---

## 6. Reglas de uso de IA que aplican

- **DevLog obligatorio por sesión con IA**, antes del push (`vault/_DevLog/YYYY-MM-DD-diana-alvarez-*.md`).
- **Revisión línea por línea** de todo código generado por IA: es responsable de lo que sube.
- **Prohibido pegar en un prompt**: `.env`, datos reales, credenciales o tokens.
- **Nunca commit directo a `main`**: todo entra por PR desde su rama fija `dev/diana-alvarez`.
- **Una sola rama, permanente.** No se abre otra por historia, sprint ni tema; no se borra
  al mergear. Se sincroniza con `git merge origin/main` antes de trabajar y antes del PR.
- **Nunca `rebase` ni `--force`** sobre `dev/diana-alvarez`.
- Commits en Conventional Commits con el ID de la historia.
- No trabajar fuera de este alcance: el CI reprueba el PR que toca archivos ajenos.
  Para cambiar algo de otra persona, pedírselo a su dueño y que lo lleve en su rama.

---

## 7. Contexto técnico específico

- Medallón: Bronze (raw + `_ingested_at`/`_source`/`_source_url`, idempotente) → Silver (tipado, CCT homologado, Great Expectations) → Gold (estrella + cubos + `features_escuela`).
- `SCOPE_ENTIDADES = ["09","15","19","14"]` (Gold y modelos); Bronze/Silver nacionales.
- Regla **`SIN_DATO`** explícito (nunca cero ni nulo). Se calcula `indice_completitud_drivers`.
- Llaves: **CCT** (escuela) y **clave INEGI de 5 dígitos** (municipio).
- Contrato con ML: features validadas con **partición temporal, nunca aleatoria**.

---

## 8. Prompts iniciales sugeridos (agnósticos de LLM)

> Funcionan en Claude Code, ChatGPT, Gemini o Copilot. Todo lo generado se revisa antes de
> commitear, y cada sesión genera DevLog.

**Contexto para pegar al inicio de la sesión:**
```
Soy de Data Engineering en FARO (bronze/silver/gold en Postgres, Airflow, dbt, Great Expectations). Alcance Gold: CDMX, Edomex, Nuevo Leon, Jalisco. Llaves: CCT y clave INEGI de municipio a 5 digitos. SIN_DATO explicito (nunca cero ni nulo). Responde en espanol con codigo comentado.
```

**Modelo medallón:**
```
Actua como arquitecto de datos. Disena el contrato bronze/silver/gold para FARO con SCOPE_ENTIDADES y politica SIN_DATO. Entrega DDL comentado.
```

**dbt:**
```
Escribe modelos dbt <capa> con tipado, deduplicacion por <LLAVE>, homologacion de municipio a 5 digitos INEGI y tests not_null/unique.
```

**Great Expectations:**
```
Genera una suite de Great Expectations para <TABLA>: nulos, unicidad de la llave, rangos fisicos y catalogos validos. Explica cada expectativa.
```
