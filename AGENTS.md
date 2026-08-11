---
id: DOC-AGENTS
title: "AGENTS.md — Protocolo para asistentes de IA"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
version: "1.0"
source_of_truth: true
traces_up: ["00_Start_Here/PROJECT_INDEX"]
tags: [ai-governance, agents, handoff]
---

# AGENTS.md — Protocolo para cualquier asistente de IA

> Lo leen Claude Code, Codex, Cursor, Gemini CLI, OpenCode, Copilot y cualquier otro harness.
> Complementa [[CLAUDE]] (contexto del proyecto) y [[_Meta/Vault_Rules]] (reglas del vault).

## 1. Orden de lectura obligatorio al iniciar sesión

Cualquier agente que abra este repositorio debe leer, en este orden:

1. **`CLAUDE.md`** — qué es el proyecto, arquitectura, alcance, equipo
2. **`_Meta/Vault_Rules.md`** — las 7 reglas no negociables
3. **`_Meta/Definition_of_Filed.md`** — cuándo un artefacto está terminado
4. **Este archivo** — protocolo de trabajo y de handoff
5. **`_DevLog/`** — la entrada más reciente, para saber dónde se quedó la sesión anterior
6. **`graphify-out/GRAPH_REPORT.md`** — si existe, el mapa estructural del proyecto

Solo después de eso, empezar a leer archivos individuales.

## 1.bis Apuntadores por herramienta

Cada asistente lee un archivo distinto por convención de su harness, pero **todos redirigen a este
`AGENTS.md`** como documento canónico. Si tu herramienta no está en la lista, lee `AGENTS.md` a mano.

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
- **Nunca** credenciales, `.env`, datos reales ni archivos >5 MB en el repositorio.
- **Toda sesión con IA genera una entrada de DevLog antes del push.**
- Todo artefacto cumple Definition of Filed: ID, carpeta, frontmatter, `_index`, matriz.
- Respeta el `Agent_Context` de la persona con la que trabajas
  (`09_AI_Governance/Agent_Contexts/{nombre}-agent-context.md`): no trabajes fuera de su alcance.

## 4. LLM Handoff Protocol

> **Cuándo aplicarlo:** cuando el contexto esté por agotarse, cuando se cambie de harness o LLM,
> o al terminar una sesión de trabajo.

Genera un archivo en `_DevLog/YYYY-MM-DD-handoff-<tema>.md` con esta estructura exacta:

```markdown
## Handoff — <fecha> — <harness usado>

- **Current objective:**
- **Current branch:**
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
2. Lee el handoff más reciente de `_DevLog/`
3. Verifica el estado real: `git status`, `git log --oneline -5`,
   `python3 _Meta/scripts/vault_lint.py .`
4. Confirma con la persona qué sigue **antes** de generar código
5. No asumas que lo del handoff ya está commiteado: verifícalo
