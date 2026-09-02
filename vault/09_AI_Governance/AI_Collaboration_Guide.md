---
id: DOC-AICOLLAB
title: "AI Collaboration Guide"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
tags: [ai, collaboration]
---

# AI Collaboration Guide — FARO

> Cómo trabajar con agentes de IA (Claude Code, Codex, Gemini, Cursor…). → [[vault/09_AI_Governance/_index]]

## Antes de cada sesión
1. Lee tu `Agent_Contexts/{identidad}-agent-context.md` (qué puedes tocar). La versión que el CI
   verifica es `vault/_Meta/ownership.yml`.
2. Confirma la `TASK-###` y el `REQ-###` asociado.
3. El repo tiene `CLAUDE.md`/`AGENTS.md` que apunta a este vault.

## Durante
- Sal siempre de tu rama fija `dev/{identidad}`, sincronizada con `git merge origin/main`.
- Commits Conventional con el ID de la historia.
- No tocar archivos 🔴.

## Al terminar (obligatorio)
- Escribir DevLog ([[vault/_Templates/DevLog_template]]) antes del push.
- Abrir PR con el template y el título estándar; nunca mergear el agente.
- Tras el merge, **no borrar la rama**: es permanente.

## Skills útiles (Claude Code)
| Skill | Cuándo |
|---|---|
| `/review` | antes de aprobar un PR |
| `/security-review` | antes de cada deploy |
| `/simplify` | tras terminar una feature |

## Qué NO debe hacer un agente
- Mergear solo · tocar secretos/prod · modificar reglas de datos/CI sin revisión humana.
