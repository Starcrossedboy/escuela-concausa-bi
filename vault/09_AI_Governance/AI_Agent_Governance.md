---
id: DOC-AIGOV
title: "AI Agent Governance"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [ai, agents, governance, security]
---

# AI Agent Governance — FARO

> Límites y reglas de los agentes IA en el flujo de desarrollo. → [[vault/09_AI_Governance/_index]]

## Principios de gobernanza
| Principio | Descripción |
|---|---|
| Evaluar antes de delegar | ¿El agente tiene el contexto? ¿el error sería catastrófico? |
| Action space restringido | Acceso solo a lo necesario para su tarea |
| Audit trail obligatorio | Cada acción deja artefacto (comentario PR + DevLog) |
| Kill-switch disponible | Todo agente puede detenerse en < 5 min |
| Humano en el loop para merges | Ningún agente mergea a la rama protegida sin aprobación |

## Reglas no negociables
- 🚫 **Ningún agente mergea a la rama principal** sin aprobación humana explícita.
- 📋 Toda sesión de IA genera **DevLog** antes del push.
- 🔒 Los agentes **no** acceden a secretos ni a producción.
- 🛑 Kill-switch documentado (cancelar workflow / Ctrl+C / deshabilitar schedule).
- 🔴 Cambios a seguridad, reglas de datos o CI/CD requieren revisión humana del dueño.

## Ownership de archivos por colaborador
Cada persona tiene un `Agent_Contexts/{identidad}-agent-context.md` con archivos 🟢 propios /
🟡 compartidos /
🔴 prohibidos. El agente **debe leerlo al inicio de cada sesión** y **detenerse** si va a tocar un 🔴.

## Checklist antes de activar un agente nuevo
- [ ] Acceso mínimo necesario
- [ ] Humano revisa su output antes de tener efecto
- [ ] Kill-switch documentado
- [ ] Genera audit trail
- [ ] Probado en staging
- [ ] Owner notificado

## Kill-switch (proceso)
1. Cancelar el workflow / `Ctrl+C` / deshabilitar el schedule.
2. Notificar al owner.
3. Registrar incidente en [[vault/10_Risk_Governance/Incident_Log]].
