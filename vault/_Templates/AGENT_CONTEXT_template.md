---
id: AGENTCTX-{IDENTIDAD-EN-MAYUSCULAS}
title: "Agent Context — {Nombre completo}"
owner: "{Nombre completo}"
status: draft
traces_up: ["vault/12_Roadmap_Sprints/Sprints/{n}-{nombre-completo-kebab}"]
tags: [ai, agent-context, ownership, celula-{n}]
---

# Agent Context — {Nombre completo}

> El agente IA de esta persona **debe leer este archivo al inicio de cada sesión**.
> Define qué puede tocar. Si va a modificar un archivo 🔴, **debe detenerse y avisar**.
> → [[vault/09_AI_Governance/AI_Agent_Governance]] · Plan: `[[vault/12_Roadmap_Sprints/Sprints/{n}-{nombre-completo-kebab}]]`

---

## 1. Identificación

| | |
|---|---|
| **Nombre** | {Nombre completo} |
| **Identidad** | `{primer-nombre}-{apellido-paterno}` |
| **Rama fija** | `dev/{identidad}` |
| **Célula** | Celula {n} — {área} |
| **Nivel** | {Alto / Medio / Bajo} |
| **Rol** | {rol} |
| **Tech Lead de la célula** | {nombre del Tech Lead} |
| **Quién revisa su código** | Edgar Edmundo Coronel Navarrete (PM) — compuerta única (DEC-003). {Tech Lead} revisa como apoyo, no bloquea |
| **Requisito(s) que cubre** | REQ-### |

---

## 2. 🟢 Alcance permitido (crear y modificar con IA libremente)

- `ruta/**`
- Su propio plan de sprint y su DevLog en `vault/_DevLog/`.

> Definido en `vault/_Meta/ownership.yml`, que es lo que el CI verifica en cada PR.
> Si esta lista y ese archivo no coinciden, **manda el archivo**.

---

## 3. 🟡 Compartidos (coordinar con el dueño antes de tocar)

| Archivo / artefacto | Dueño | Protocolo |
|---|---|---|
| `ruta/**` | {dueño} | coordinar antes de tocar |
| `vault/02_Requirements/Traceability_Matrix.md` | PM — Edgar Coronel | actualiza su fila; el PM consolida |
| `_index.md` de las carpetas que toca | PM / dueño de carpeta | registrar cada artefacto nuevo |

---

## 4. 🔴 Fuera de alcance (nunca tocar con IA sin autorización)

| Ruta / área | Dueño | A quién pedir |
|---|---|---|
| `ruta/**` | {célula} — {dueño} | pedir a {área} |

> Todo lo que no esté en 🟢 ni en 🟡 es 🔴. El CI reprueba el PR que salga del alcance.

---

## 5. Historias asignadas

| ID | Historia | Sprint |
|---|---|---|
| `US-###` | {título} | S# |

---

## 6. Reglas de uso de IA que aplican

- **DevLog obligatorio por sesión con IA**, antes del push (`vault/_DevLog/YYYY-MM-DD-{identidad}-*.md`).
- **Revisión línea por línea** de todo código generado por IA: es responsable de lo que sube.
- **Prohibido pegar en un prompt**: `.env`, datos reales, credenciales o tokens.
- **Nunca commit directo a `main`**: todo entra por PR desde su rama fija `dev/{identidad}`.
- **Una sola rama, permanente.** No se abre otra por historia, sprint ni tema; no se borra
  al mergear. Se sincroniza con `git merge origin/main` antes de trabajar y antes del PR.
- **Nunca `rebase` ni `--force`** sobre `dev/{identidad}`.
- Commits en Conventional Commits con el ID de la historia.
- No trabajar fuera de este alcance: el CI reprueba el PR que toca archivos ajenos.
  Para cambiar algo de otra persona, pedírselo a su dueño y que lo lleve en su rama.

---

## 7. Contexto técnico específico

- {lo que el agente necesita saber del dominio de esta persona}

---

## 8. Prompts iniciales sugeridos (agnósticos de LLM)

```
Lee AGENTS.md, vault/_Meta/ownership.yml y este Agent Context.
Trabajo en la rama dev/{identidad} y solo toco los archivos de mi alcance 🟢/🟡.
Vamos con {US-###}: {objetivo}.
```
