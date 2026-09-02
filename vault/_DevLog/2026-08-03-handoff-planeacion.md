---
project: "FARO"
date: "2026-08-03"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "sesión de planeación (handoff)"
touches: ["PRD-GENERAL","PRD","REQ-001","REQ-007","US-CATALOG","DS-01","DS-08","PLAN-MAESTRO","DOC-DATAMODEL","DOC-AGENTS"]
tags: [devlog, handoff, planeacion]
---

# Handoff — 2026-08-03 — planeación

→ [[vault/_DevLog/_index|Volver al índice]] · Protocolo: [[AGENTS]] §4

## Handoff — 2026-08-03 — Claude Code (Opus 4.8)

- **Current objective:** cerrar la **capa de planeación y gobernanza** del vault FARO (producto,
  requisitos, fuentes, historias, gobernanza de IA y modelo de datos) antes de escribir código.
- **Current branch:** `main`. **Los cambios NO están en una rama de PR todavía** (hay cambios sin
  commitear; ver §Risks). El PR se hará cuando todo esté listo para arrancar, por decisión del PM.
- **Latest graph status:** **grafo parcial (`--code-only`)** generado con **Graphify v0.9.32** (instalado
  vía `pipx`). Automatización ya configurada (`.github/workflows/update-project-graph.yml`,
  `.graphifyignore`). El **grafo completo (docs + código) queda pendiente para el Sprint 2**, cuando
  exista código real en `src/`: hoy solo hay **1 archivo de código** y grafar los **75 documentos**
  exigiría API key y consumo de tokens sin aportar valor todavía.
- **Relevant Graphify queries:** ninguna aún de valor (el grafo `--code-only` cubre 1 archivo). Cuando
  haya código en `src/`, empezar por `graphify explain "vault/03_Architecture/Data_Model"` y
  `graphify query "que alimenta features_escuela"`.
- **Files changed (por área, lo cerrado hoy):**
  - **Producto:** `vault/01_Product/PRD_General_Materia.md` (frontmatter `PRD-GENERAL`), `vault/01_Product/PRD.md`
    (PRD FARO completo y autosuficiente), `vault/01_Product/_index.md`.
  - **Requisitos:** `vault/02_Requirements/Requirements_Detailed.md` (7 REQ con 39 AC verificables),
    `vault/02_Requirements/User_Stories.md` (catálogo de 87 historias), `vault/02_Requirements/_index.md`.
  - **Fuentes:** `vault/14_Data_Sources/DS-01…DS-08` (8 notas) + `vault/14_Data_Sources/_index.md`.
  - **Roadmap:** `vault/12_Roadmap_Sprints/PLAN_MAESTRO.md` (frontmatter v1.2), `Sprints/_index.md`, y los
    **21 planes de sprint** (partición de historias compartidas + rebalanceo Célula 3).
  - **Gobernanza IA:** `vault/09_AI_Governance/Agent_Contexts/` — **21 Agent Contexts** + `_index.md`.
  - **Arquitectura:** `vault/03_Architecture/Data_Model.md` (medallón completo, US-101) + `_index.md`.
  - **Raíz:** `AGENTS.md` registrado en `vault/00_Start_Here/PROJECT_INDEX.md`.
  - **Homologación:** grafía acentuada del nombre canónico en 42 archivos (planes + Agent Contexts).
- **IDs touched:** `PRD-GENERAL`, `PRD`, `REQ-001`…`REQ-007`, `US-CATALOG` (87 US, incl. particiones
  US-121a/b…, US-211a/b, US-521a/b/c y rebalanceo US-304a/304b/324/325), `DS-01`…`DS-08`,
  `PLAN-MAESTRO`, `DOC-DATAMODEL`, `DOC-AGENTS`, `AGENTCTX-*` (21).
- **Decisions made:**
  1. Dos PRD canónicos distintos: `PRD-GENERAL` = QUÉ (rúbrica del profesor, inmutable) · `PRD` = CÓMO
     (proyecto FARO); `PRD` traza a `PRD-GENERAL`.
  2. Un `REQ-###` por módulo de rúbrica (7 REQ = 10 pts); cobertura 7/7 por las 87 historias.
  3. Historias compartidas **partidas por artefacto** (fuente / dashboard / servicio) → 1 responsable
     por historia; **87 únicas = 87 asignaciones**.
  4. Célula 3 rebalanceada: US-304 dividida (diseño→Andrés / recuperación→Carlos) + US-324/US-325.
  5. Agent Contexts nombrados `{nombre}-agent-context.md`; scope 🟢/🟡/🔴 por célula.
  6. `Data_Model.md`: `SCOPE_ENTIDADES` se aplica en Silver→Gold; owner = Diana (US-101).
  7. Nombre canónico **acentuado** único por persona en todo el vault.
- **Open questions:**
  - ¿`Álvarez`/`Benítez` deben acentuarse también? (hoy se mantuvieron sin acento por coincidir con el
    catálogo). Si sí, es una pasada repo-wide.
  - REQ de US-324 (model cards) y US-325 (sesgo): se mapearon a REQ-003; ¿o REQ-007/REQ-001?
  - ¿`dim_escuela` con infraestructura embebida o una `dim_infraestructura` aparte?
- **Risks:**
  - ~~`vault_lint` en ROJO por `GEMINI.md` sin frontmatter.~~ **RESUELTO:** `GEMINI.md` recibió
    frontmatter (`DOC-GEMINI`) y quedó registrado; `.cursorrules` y `.github/copilot-instructions.md`
    documentados en `PROJECT_INDEX.md` y en `AGENTS.md` §1.bis. Linter en verde.
  - Trabajo aún en `main` sin rama de PR; regla del vault: **nunca push directo a `main`**.
  - Rutas de código (`src/`, `dbt/`, `dags/`, `superset/`) son convención a futuro; aún no existen.
- **Tests executed:**
  - `python3 vault/_Meta/scripts/vault_lint.py .` → **✅ Vault limpio** (tras resolver `GEMINI.md`).
  - `git status` → cambios sin commitear de la sesión (planeación + apuntadores multi-LLM); pendientes
    de rama + PR.
- **Next recommended action:**
  1. Falta por planear: `vault/03_Architecture/System_Design.md`, primer(os) **ADR**, y la
     **Traceability_Matrix** (se siembra al final, cuando existan todos los artefactos a enlazar).
     *(`API_Specification.md` ya quedó cerrado — US-401.)*
  2. **Graphify:** grafo `--code-only` ya generado con v0.9.32 (pipx). **Correr el grafo completo
     (docs + código) hasta el Sprint 2**, cuando haya código real en `src/`; hoy no aporta valor (1
     archivo de código, 75 docs, requeriría API key y tokens).
  3. Cuando todo esté Filed y el linter verde: **DevLog de cierre + rama `docs/...` + PR** (nunca push
     directo a `main`).

## Estado de "lo cerrado hoy" (checklist)

- [x] PRD general (`PRD-GENERAL`) con frontmatter y registrado
- [x] PRD del proyecto FARO (`PRD`) completo y autosuficiente
- [x] 7 requisitos `REQ-001…007` con 39 criterios de aceptación verificables
- [x] 8 fuentes `DS-01…DS-08` documentadas (prueba de descarga PENDIENTE — Semana 1)
- [x] Catálogo de **87 historias** (`US-CATALOG`), 1 responsable c/u, 7/7 REQ cubiertos
- [x] **21 Agent Contexts** con scope 🟢/🟡/🔴 por persona
- [x] `Data_Model.md` — arquitectura medallón completa (US-101)
- [x] `AGENTS.md` registrado en el índice del proyecto
- [x] Graphify v0.9.32 instalado (pipx) + configurado (workflow + `.graphifyignore`); grafo `--code-only` generado. Grafo completo → Sprint 2 (cuando haya código en `src/`)
- [x] Apuntadores multi-LLM consistentes (`GEMINI.md` con frontmatter, `.cursorrules` y `copilot-instructions.md` documentados; tabla en AGENTS.md §1.bis)
- [x] `vault_lint` verde
- [x] API_Specification (US-401) — contrato que desbloquea a C2 y C3
- [ ] System_Design · ADRs
- [ ] Traceability_Matrix sembrada
- [ ] DevLog de cierre + rama + PR
