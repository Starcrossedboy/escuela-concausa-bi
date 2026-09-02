---
id: DOC-AGENTS
title: "AGENTS.md — Protocolo para asistentes de IA"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
version: "1.0"
source_of_truth: true
traces_up: ["vault/00_Start_Here/PROJECT_INDEX"]
tags: [ai-governance, agents, handoff]
---

# AGENTS.md — Protocolo para cualquier asistente de IA

> Lo leen Claude Code, Codex, Cursor, Gemini CLI, OpenCode, Copilot y cualquier otro harness.
> Complementa [[CLAUDE]] (contexto del proyecto) y [[vault/_Meta/Vault_Rules]] (reglas del vault).

## 1. Orden de lectura obligatorio al iniciar sesión

**Este archivo es el documento canónico y el único que declara el orden de lectura.** Los demás
apuntadores (`GEMINI.md`, `.cursorrules`, `.github/copilot-instructions.md`) solo redirigen aquí;
ninguno repite el orden, para que no puedan desincronizarse.

Cualquier agente que abra este repositorio debe leer, en este orden:

1. **Este archivo** — protocolo de trabajo, ramas y handoff
2. **`CLAUDE.md`** — qué es el proyecto, arquitectura, alcance, equipo
3. **`vault/_Meta/Vault_Rules.md`** — las 9 reglas no negociables
4. **`vault/_Meta/ownership.yml`** — quién es quién, su rama y su alcance
5. **`vault/_Meta/Definition_of_Filed.md`** — cuándo un artefacto está terminado
6. **`vault/_DevLog/`** — la entrada más reciente, para saber dónde se quedó la sesión anterior
7. **`graphify-out/GRAPH_REPORT.md`** — si existe, el mapa estructural del proyecto

Solo después de eso, empezar a leer archivos individuales.

## 1.bis Apuntadores por herramienta

Cada asistente lee un archivo distinto por convención de su harness, pero **todos redirigen a este
`AGENTS.md`** como documento canónico y ninguno duplica sus reglas. Si tu herramienta no está en la
lista, lee `AGENTS.md` a mano.

| Asistente | Archivo que lee | `.md` del vault |
|---|---|---|
| Claude Code | `CLAUDE.md` | sí (contexto del proyecto) |
| Codex / genérico | `AGENTS.md` | sí (este archivo, canónico) |
| Gemini CLI | `GEMINI.md` | sí (apuntador) |
| Cursor | `.cursorrules` | no |
| GitHub Copilot | `.github/copilot-instructions.md` | no |
| Otros harness | — | leer `AGENTS.md` manualmente |

## 2. Consulta el grafo antes de leer archivos

Cuando exista `graphify-out/`, úsalo antes de abrir archivos a ciegas:

| Necesitas | Comando |
|---|---|
| Entender qué controla algo | `graphify query "que parte del proyecto controla X"` |
| Ver la relación entre dos piezas | `graphify path "ComponenteA" "ComponenteB"` |
| Entender un módulo | `graphify explain "nombre-del-modulo"` |
| Analizar impacto de un cambio | `graphify prs` |

**No hagas grep masivo ni leas decenas de archivos si el grafo puede responder primero.**
Trata `graphify-out/graph.json` como el mapa estructural más actualizado del proyecto.

## 3. Reglas de trabajo (resumen — el detalle está en Vault_Rules)

- **Nunca push directo a `main`.** Todo por PR con 1 aprobación del PM (compuerta única, ver DEC-003).
- **Una sola rama por persona: `dev/{identidad}`**, donde la identidad es
  `{primer-nombre}-{apellido-paterno}` en minúsculas y sin acentos. Es permanente: no se borra al
  mergear y no se abre otra por historia, sprint ni tema.
- **Sincroniza con `git merge origin/main`** antes de trabajar y otra vez antes de abrir el PR.
  Nunca `rebase`, nunca `--force` sobre `dev/*`.
- Título del PR: `[Nombre Apellido] - Descripción concisa (ID) - [sync|CI|DoF|DevLog]`.
- **Nunca** credenciales, `.env`, datos reales ni archivos >5 MB en el repositorio.
- **Toda sesión con IA genera una entrada de DevLog antes del push.**
- Todo artefacto cumple Definition of Filed: ID, carpeta, frontmatter, `_index`, matriz.
- Respeta el alcance de la persona con la que trabajas: su `Agent_Context`
  (`vault/09_AI_Governance/Agent_Contexts/{identidad}-agent-context.md`) y el padrón
  `vault/_Meta/ownership.yml`, que es el que hace cumplir el CI. **No trabajes fuera de su alcance.**

## 4. LLM Handoff Protocol

> **Cuándo aplicarlo:** cuando el contexto esté por agotarse, cuando se cambie de harness o LLM,
> o al terminar una sesión de trabajo.

Genera un archivo en `vault/_DevLog/YYYY-MM-DD-handoff-<tema>.md` con esta estructura exacta:

```markdown
## Handoff — <fecha> — <harness usado>

- **Current objective:**
- **Current branch:**            (siempre `dev/{identidad}`)
- **Latest graph status:**        (fecha del último `graphify update`, o "sin grafo aún")
- **Relevant Graphify queries:**  (las consultas que dieron contexto útil)
- **Files changed:**
- **IDs touched:**                (REQ / US / DS / ML / ADR / TEST)
- **Decisions made:**
- **Open questions:**
- **Risks:**
- **Tests executed:**             (comandos y resultado, incluido vault_lint.py)
- **Next recommended action:**
```

**El siguiente agente arranca leyendo el handoff más reciente**, no reconstruyendo el contexto
desde cero. Ese es todo el punto: que un límite de tokens no detenga el proyecto.

## 5. Si eres el siguiente agente

1. Lee el orden de la sección 1
2. Lee el handoff más reciente de `vault/_DevLog/`
3. Verifica el estado real: `git status`, `git log --oneline -5`,
   `python3 vault/_Meta/scripts/vault_lint.py .`
4. Confirma con la persona qué sigue **antes** de generar código
5. No asumas que lo del handoff ya está commiteado: verifícalo
