---
project: "FARO"
date: "2026-08-06"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Codex"
model: "GPT-5"
session_duration: "preparación del directorio GitHub y CODEOWNERS"
touches: ["DOC-ONBOARD", "US-003", "US-004", "REQ-007", "RPT-PM-SPEC", "TEST-002", "DEC-002"]
tags: [devlog, onboarding, github, codeowners, dashboard, governance]
---

# DevLog — 2026-08-06 — directorio GitHub y CODEOWNERS

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/00_Start_Here/Developer_Onboarding|Directorio del equipo]]

## Qué se hizo

- Se incorporaron al onboarding los 21 integrantes con nivel canónico, célula y usuario de GitHub.
- Se dejaron explícitamente pendientes los usuarios de Emilio Galnares Ruiz, Carlos Guillermo
  Mayorga Tapia y Oscar Antonio Quiroz Lázaro.
- Se sustituyeron los cinco placeholders de Tech Leads en `.github/CODEOWNERS` con los usuarios
  proporcionados por el PO.
- Se corrigió el nombre de la carpeta del repositorio en el setup y el resumen del flujo volvió a
  reflejar la política canónica de dos aprobaciones.
- Se registró como [[vault/10_Risk_Governance/Decision_Log|DEC-002]] la excepción temporal de una
  aprobación, con restauración prevista para el 2026-08-07.
- Se restauró la pestaña **Equipo** sin retirar **Plan por persona**, con color estable por célula,
  directorio GitHub, 87 US asignadas y conteos de PR por autor.
- Se enlazó `Developer_Onboarding → generador → snapshot JSON → HTML → especificación → TEST-002`
  y se incorporó el directorio al fingerprint y al trigger del workflow.
- Se excluyó `github-activity.json` de Git para conservarlo como snapshot efímero del artifact.
- Se restauró la cuenta regresiva visible hacia la entrega del 9 de septiembre; la fecha, etiqueta y
  zona horaria ahora viven en el frontmatter del Plan Maestro y el navegador recalcula los días.

## 🤖 Sesión de IA

- **Agente / modelo:** Codex / GPT-5.
- **Archivos creados/modificados:** onboarding, `CODEOWNERS`, decisión, especificación, plantilla y
  artefactos del tablero, scripts de generación/actividad/validación, workflow, prueba e índices.
- **Decisiones autónomas:** conservar nivel Medio para Juan Carlos porque es el valor de las fuentes
  canónicas; marcar la discrepancia para resolución humana; conservar literalmente los usuarios
  recibidos, sujetos a validación al invitar.
- **Correcciones manuales:** pendientes de la sesión del equipo.
- **Prompt inicial:** preparar la información de integrantes y dejar listos los tres usuarios faltantes.

## Seguridad / calidad

- [x] Sin secretos hardcodeados.
- [x] Los cambios documentales quedan enlazados desde el onboarding y el índice del DevLog.
- [x] `CODEOWNERS` queda sujeto a revisión explícita de Luis Téllez / Célula 5.

## Bloqueantes

- Faltan los usuarios de GitHub de Emilio, Carlos y Oscar.
- Debe verificarse en GitHub la escritura exacta de todas las cuentas antes de enviar invitaciones.
- La tabla recibida marca a Juan Carlos como Bajo, mientras las fuentes canónicas lo marcan Medio.

## Próximos pasos

- Completar los tres usuarios pendientes después de la sesión del 2026-08-06.
- Confirmar o corregir la discrepancia de nivel de Juan Carlos en todas las fuentes relacionadas.
- Solicitar revisión C5 de `.github/CODEOWNERS` y restaurar dos aprobaciones el 2026-08-07.

## Handoff — 2026-08-06 — Codex

- **Current objective:** pestaña Equipo restaurada y enlazada, pendiente de confirmaciones humanas y
  actualización del PR.
- **Current branch:** `feat/edgar-tablero-control-v2`.
- **Latest graph status:** actualizado el 2026-08-06 desde el working tree; 529 nodos, 539 aristas y
  72 comunidades; base Git `71f81168`.
- **Relevant Graphify queries:** consultas sobre directorio GitHub/personas/historias/tablero y fecha
  de entrega; `path` entre `parse_github_directory()` y `write_outputs()`; `explain build_snapshot()`.
- **Files changed:** onboarding, CODEOWNERS, workflow, especificación/plantilla/HTML/JSON del tablero,
  colector/generador/validador, trazabilidad, prueba, decisión, índices, `.gitignore` y Graphify.
- **IDs touched:** DOC-ONBOARD, US-003, US-004, REQ-007, RPT-PM-SPEC, TEST-002, DEC-002.
- **Decisions made:** la pestaña Equipo y Plan por persona permanecen separadas; PR sin snapshot se
  muestra como “sin datos”, nunca como cero; GitHub no determina Done; el contador usa días
  calendario en `America/Mexico_City` y no una hora de entrega inventada.
- **Open questions:** usuarios de Emilio/Carlos/Oscar; nivel de Juan Carlos; ampliar o conservar las
  exclusiones documentales de `.graphifyignore`.
- **Risks:** cuentas sin acceso producen CODEOWNERS inefectivo; el conteo local de PR requiere el
  artifact de Actions; el cambio `.github/**` necesita revisión C5.
- **Tests executed:** generador ✅; TEST-002 ✅; `vault_lint.py` ✅; `py_compile` ✅; sintaxis JS con
  `node --check` ✅; contador dinámico y fuente de entrega en TEST-002 ✅; `git diff --check` ✅;
  21 personas/87 US/18 usuarios/3 pendientes verificados ✅; Graphify actualizado ✅. La inspección
  visual automatizada de `file://` quedó bloqueada por la
  política del navegador local y debe confirmarse recargando la pestaña abierta.
- **Next recommended action:** revisión visual humana, completar tres usuarios, resolver nivel de
  Juan Carlos, revisión C5, stage/commit/push del mismo branch y restaurar dos aprobaciones.
