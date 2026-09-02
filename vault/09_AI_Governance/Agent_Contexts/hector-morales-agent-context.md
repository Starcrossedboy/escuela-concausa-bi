---
id: AGENTCTX-HECTOR-MORALES
title: "Agent Context — Héctor Rafael Morales Marbán"
owner: "Héctor Rafael Morales Marbán"
status: approved
traces_up: ["vault/12_Roadmap_Sprints/Sprints/3-hector-rafael-morales-marban"]
tags: [ai, agent-context, ownership, celula-3]
---

# Agent Context — Héctor Rafael Morales Marbán

> El agente IA de esta persona **debe leer este archivo al inicio de cada sesión**.
> Define qué puede tocar. Si va a modificar un archivo 🔴, **debe detenerse y avisar**.
> → [[vault/09_AI_Governance/AI_Agent_Governance]] · Plan: [[vault/12_Roadmap_Sprints/Sprints/3-hector-rafael-morales-marban]]

---

## 1. Identificación

| | |
|---|---|
| **Nombre** | Héctor Rafael Morales Marbán |
| **Identidad** | `hector-morales` |
| **Rama fija** | `dev/hector-morales` — permanente, no se borra al mergear |
| **Célula** | Celula 3 — Machine Learning & AI Agent |
| **Nivel** | Medio |
| **Rol** | Cientifico de datos · Modelos supervisados |
| **Tech Lead de la célula** | Andrés González Habib |
| **Quién revisa su código** | Edgar Edmundo Coronel Navarrete (PM) — compuerta única (DEC-003). Andrés González Habib (Tech Lead) revisa como apoyo, no bloquea |
| **Requisito(s) que cubre** | REQ-003 (3 modelos de ML) y REQ-006 (agente conversacional) |

---

## 2. 🟢 Alcance permitido (crear y modificar con IA libremente)

- `src/modelos/**`
- `src/agente/**`
- `vault/15_ML_Models/**`
- `notebooks/**`
- Su propio plan de sprint y su DevLog en `vault/_DevLog/`.

> Definido en `vault/_Meta/ownership.yml`, que es lo que el CI verifica en cada PR.
> Si esta lista y ese archivo no coinciden, **manda el archivo**.

---

## 3. 🟡 Compartidos (coordinar con el dueño antes de tocar)

| Archivo / artefacto | Dueño | Protocolo |
|---|---|---|
| `tests/**` | dueño del área | cambio acotado; avisar en el PR |
| `vault/06_Quality_Testing/Automated/**` | dueño del área | cambio acotado; avisar en el PR |
| `gold.features_escuela` | Diana Alvarez (C1) | contrato de features versionado (US-104) |
| Endpoints de inferencia ML | Christian Ruiz (C4) | acordar contrato de request/response |
| Tabla de predicciones → Gold | Diana Alvarez (C1) | acordar reincorporación a Gold |
| `vault/02_Requirements/Traceability_Matrix.md` | PM — Edgar Coronel | actualiza su fila; el PM consolida |
| `_index.md` de las carpetas que toca | PM / dueño de carpeta | registrar cada artefacto nuevo |

---

## 4. 🔴 Fuera de alcance (nunca tocar con IA sin autorización)

| Ruta / área | Dueño | A quién pedir |
|---|---|---|
| `src/ingesta/**`, `dbt/**`, `dags/**` | C1 — Diana Alvarez | pedir a Data Eng |
| `src/api/**` | C4 — Christian Ruiz | pedir a Backend |
| `superset/**` | C2 — Manuel Serranía | pedir a BI |
| `.github/**` | C5 — Luis Téllez | pedir a DevOps |
| `vault/_Meta/**` | PM — Edgar Coronel | pedir al PO |
| `vault/07_Security/**` | C4 — Christian Ruiz | pedir a Seguridad |

> **Regla 7 del vault:** todo cambio de **esquema, seguridad o CI/CD** requiere **revisión
> humana explícita** antes de mergear.

---

## 5. Historias asignadas

| ID | Sprint | Objetivo |
|---|---|---|
| US-311 | S4 | Predecir variacion de matricula por escuela para el siguiente ciclo. MAE/RMSE con backtesting temporal. |
| US-312 | S5 | Tabla comparativa, curvas y analisis de error por entidad. Va a `vault/06_Quality_Testing/`. |
| US-313 | S5 | Job batch que escribe `gold.predicciones` y `gold.recomendaciones` para DB-06 y DB-09. |

---

## 6. Reglas de uso de IA que aplican

- **DevLog obligatorio por sesión con IA**, antes del push (`vault/_DevLog/YYYY-MM-DD-hector-morales-*.md`).
- **Revisión línea por línea** de todo código generado por IA: es responsable de lo que sube.
- **Prohibido pegar en un prompt**: `.env`, datos reales, credenciales o tokens.
- **Nunca commit directo a `main`**: todo entra por PR desde su rama fija `dev/hector-morales`.
- **Una sola rama, permanente.** No se abre otra por historia, sprint ni tema; no se borra
  al mergear. Se sincroniza con `git merge origin/main` antes de trabajar y antes del PR.
- **Nunca `rebase` ni `--force`** sobre `dev/hector-morales`.
- Commits en Conventional Commits con el ID de la historia.
- No trabajar fuera de este alcance: el CI reprueba el PR que toca archivos ajenos.
  Para cambiar algo de otra persona, pedírselo a su dueño y que lo lleve en su rama.

---

## 7. Contexto técnico específico

- 3 modelos: **ML-01** regresión (MAE/RMSE), **ML-02** clasificación multiclase de driver dominante con **SHAP**, **ML-03** clustering (Silhouette).
- **Validación con partición temporal, nunca aleatoria** (evitar fuga de información).
- Registro y versionado en **MLflow**; features desde `gold.features_escuela`.
- Agente **RAG/Text-to-SQL** (ChromaDB + sentence-transformers). **Nunca** ejecutar DELETE/UPDATE/DROP.

---

## 8. Prompts iniciales sugeridos (agnósticos de LLM)

> Funcionan en Claude Code, ChatGPT, Gemini o Copilot. Todo lo generado se revisa antes de
> commitear, y cada sesión genera DevLog.

**Contexto para pegar al inicio de la sesión:**
```
Soy de Machine Learning & Agente en FARO. 3 modelos (regresion, clasificacion multiclase de driver con SHAP, clustering), validacion temporal (nunca aleatoria), MLflow, y agente RAG/Text-to-SQL. Responde en espanol con codigo comentado.
```

**Modelo supervisado:**
```
Entrena <ML-01 regresion / ML-02 clasificacion> con particion temporal (nunca aleatoria). Reporta la metrica y, para ML-02, explicabilidad con SHAP.
```

**Clustering:**
```
Implementa el clustering de escuelas (ML-03): selecciona k, valida con Silhouette y perfila cada grupo en lenguaje de negocio.
```

**Agente RAG:**
```
Diseña la capa de recuperacion del agente: indexar el esquema de Gold en ChromaDB con embeddings y construir la consulta de contexto. Nunca DELETE/UPDATE/DROP.
```
