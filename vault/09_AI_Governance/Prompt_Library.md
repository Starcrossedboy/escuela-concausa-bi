---
id: DOC-PROMPTLIB
title: "Prompt Library"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
tags: [ai, prompts]
---

# Prompt Library — FARO

> Prompts reutilizables y probados. → [[vault/09_AI_Governance/_index]]

## Plantilla de prompt de tarea
```
Contexto: lee vault/09_AI_Governance/Agent_Contexts/{nombre}.md y vault/02_Requirements/Requirements_Detailed (REQ-###).
Tarea: <objetivo>.
Restricciones: solo tocar archivos 🟢; no mergear; escribir DevLog al final.
Definición de done: ver vault/05_Engineering/Definition_of_Done.
```

## Prompts por fase
| Fase | Prompt (resumen) |
|---|---|
| Implementación | ver plantilla arriba |
| Review | `/review` sobre el PR |
| Seguridad | `/security-review` |
