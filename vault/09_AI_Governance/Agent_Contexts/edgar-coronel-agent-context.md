---
id: AGENTCTX-EDGAR-CORONEL
title: "Agent Context — Edgar Edmundo Coronel Navarrete"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
traces_up: ["vault/12_Roadmap_Sprints/Sprints/0-edgar-edmundo-coronel-navarrete"]
tags: [ai, agent-context, ownership, celula-0]
---

# Agent Context — Edgar Edmundo Coronel Navarrete

> El agente IA de esta persona **debe leer este archivo al inicio de cada sesión**.
> Define qué puede tocar. Si va a modificar un archivo 🔴, **debe detenerse y avisar**.
> → [[vault/09_AI_Governance/AI_Agent_Governance]] · Plan: [[vault/12_Roadmap_Sprints/Sprints/0-edgar-edmundo-coronel-navarrete]]

---

## 1. Identificación

| | |
|---|---|
| **Nombre** | Edgar Edmundo Coronel Navarrete |
| **Identidad** | `edgar-coronel` |
| **Rama fija** | `dev/edgar-coronel` — permanente, no se borra al mergear |
| **Célula** | PO — Direccion de Proyecto |
| **Nivel** | Medio |
| **Rol** | Lider de Proyecto / Product Owner |
| **Tech Lead de la célula** | Edgar Edmundo Coronel Navarrete (PO) |
| **Quién revisa su código** | Compuerta única (DEC-003): sus propios PR se mergean con bypass de administrador, validados por el CI |
| **Requisito(s) que cubre** | REQ-007 (trabajo en equipo, Git y documentación) |

---

## 2. 🟢 Alcance permitido (crear y modificar con IA libremente)

- `vault/_Meta/**`
- `vault/00_Start_Here/**`
- `vault/01_Product/**`
- `vault/02_Requirements/**`
- `vault/10_Risk_Governance/**`
- `vault/12_Roadmap_Sprints/**`
- `vault/13_Reports/**`
- `vault/_DevLog/_index.md`
- Su propio plan de sprint y su DevLog en `vault/_DevLog/`.

> Definido en `vault/_Meta/ownership.yml`, que es lo que el CI verifica en cada PR.
> Si esta lista y ese archivo no coinciden, **manda el archivo**.

---

## 3. 🟡 Compartidos (coordinar con el dueño antes de tocar)

| Archivo / artefacto | Dueño | Protocolo |
|---|---|---|
| `README.md` | dueño del área | cambio acotado; avisar en el PR |
| `CLAUDE.md` | dueño del área | cambio acotado; avisar en el PR |
| `AGENTS.md` | dueño del área | cambio acotado; avisar en el PR |
| `GEMINI.md` | dueño del área | cambio acotado; avisar en el PR |
| `.cursorrules` | dueño del área | cambio acotado; avisar en el PR |
| `.github/**` | Luis Téllez (C5) | coordinar antes de tocar |
| Agent Contexts de cada persona | cada dueño | coordinar cambios de scope |
| `_index.md` de todas las carpetas | dueño de carpeta | mantener el MOC al día |

---

## 4. 🔴 Fuera de alcance (nunca tocar con IA sin autorización)

| Ruta / área | Dueño | A quién pedir |
|---|---|---|
| `src/**`, `dbt/**`, `dags/**` | células de código | el PO no escribe código de producción; coordinar con la célula |
| `superset/**` | C2 — Manuel Serranía | pedir a la Célula 2 |
| `.github/**` | C5 — Luis Téllez | pedir a la Célula 5 |

> **Regla 7 del vault:** todo cambio de **esquema, seguridad o CI/CD** requiere **revisión
> humana explícita** antes de mergear.

---

## 5. Historias asignadas

| ID | Sprint | Objetivo |
|---|---|---|
| US-001 | S1 | Repo `escuela-concausa-bi` desde cero. Reemplazar los 93 placeholders, crear `Secrets_Policy.md` (4 links rotos) y dejar `vault_lint.py` en verde. |
| US-002 | S1 | Traducir los 7 modulos de la rubrica a `REQ-###` con criterios `AC-###` verificables. |
| US-003 | S1 | Nombre canonico por persona + un `vault/09_AI_Governance/Agent_Contexts/{nombre}.md` para gobernar el uso de IA. |
| US-004 | S2 | Una fila por REQ, actualizada en cada standup. Es el tablero de control del proyecto. |
| US-005 | S4 | Un responsable por sprint que corre el linter, revisa la matriz y caza documentos huerfanos. |
| US-006 | S6 | Guion de 10 min, reparto de quien muestra que y plan B si falla la conexion. |

---

## 6. Reglas de uso de IA que aplican

- **DevLog obligatorio por sesión con IA**, antes del push (`vault/_DevLog/YYYY-MM-DD-edgar-coronel-*.md`).
- **Revisión línea por línea** de todo código generado por IA: es responsable de lo que sube.
- **Prohibido pegar en un prompt**: `.env`, datos reales, credenciales o tokens.
- **Nunca commit directo a `main`**: todo entra por PR desde su rama fija `dev/edgar-coronel`.
- **Una sola rama, permanente.** No se abre otra por historia, sprint ni tema; no se borra
  al mergear. Se sincroniza con `git merge origin/main` antes de trabajar y antes del PR.
- **Nunca `rebase` ni `--force`** sobre `dev/edgar-coronel`.
- Commits en Conventional Commits con el ID de la historia.
- No trabajar fuera de este alcance: el CI reprueba el PR que toca archivos ajenos.
  Para cambiar algo de otra persona, pedírselo a su dueño y que lo lleve en su rama.

---

## 7. Contexto técnico específico

- Gobierno del vault: `Vault_Rules`, `Naming_Conventions`, **Definition of Filed**.
- Trazabilidad **REQ → US → TEST → Release**; la `Traceability_Matrix` es la fuente viva.
- Conventional Commits con ID de historia; **nunca push directo a `main`**.
- Rúbrica de 10 pts; sin URL pública viva al evaluar, el techo es 6.0.

---

## 8. Prompts iniciales sugeridos (agnósticos de LLM)

> Funcionan en Claude Code, ChatGPT, Gemini o Copilot. Todo lo generado se revisa antes de
> commitear, y cada sesión genera DevLog.

**Contexto para pegar al inicio de la sesión:**
```
Soy PO/PM de FARO, plataforma BI end-to-end sobre datos abiertos de Mexico. Coordino 21 personas en 5 celulas. Cuido el vault (reglas, trazabilidad, Definition of Filed) y la entrega. Responde en espanol.
```

**Trazabilidad:**
```
Ayudame a mantener la Traceability_Matrix: dado este REQ y sus US, verifica que cada US tenga TEST y este en el _index correcto. Marca huecos.
```

**DevLog:**
```
Redacta mi entrada de DevLog de hoy siguiendo vault/_Templates/DevLog_template: que se hizo, decisiones de la IA, correcciones y IDs tocados.
```

**Pitch:**
```
Ayudame a estructurar el pitch de 10 minutos de FARO: problema, tesis, demo en vivo y valor prescriptivo. Publico: profesor experto en BI/IA.
```
