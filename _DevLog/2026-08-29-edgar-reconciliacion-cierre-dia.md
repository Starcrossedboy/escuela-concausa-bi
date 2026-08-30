---
project: "FARO"
date: "2026-08-29"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "Sonnet 5"
session_duration: "larga — revisión de 15 PRs, 5 conflictos resueltos, reconciliación de cierre y guion de junta"
touches: ["US-004", "US-121a", "US-122a", "US-123a", "US-124a", "US-212", "US-213", "US-221", "US-222", "US-303", "US-321", "US-322", "US-325", "BUG-012", "BUG-017", "BUG-018", "BUG-019", "BUG-020", "BUG-026", "BUG-027", "BUG-028", "ADR-007", "PLAN-EXEC-STATUS", "RPT-JUNTA-MOCK-2026-08-29", "RPT-VAULT-FIX-2026-08-29"]
tags: [devlog, pm, status, reconciliation, meeting, bugs]
---

# DevLog — 2026-08-29 — Reconciliación de cierre y guion de la junta del mock

→ [[_DevLog/_index|Volver al índice]] · [[12_Roadmap_Sprints/Execution_Status]] ·
[[13_Reports/Junta_Mock_2026-08-29]] · [[13_Reports/Vault_Correcciones_2026-08-29]]

## Qué se hizo

Día de 14 PRs mergeados. Esta sesión cierra el estado: reconcilia `Execution_Status` con lo que de
verdad está en `main`, corrige el registro de bugs, asigna lo que estaba suelto y prepara la junta.

## Historias actualizadas

**Cerradas:** `US-121a`, `US-122a`, `US-123a`, `US-124a` (DS-06 y DS-08, Emilio), `US-213` (DB-05 y
DB-08, Monserrat), `US-221` (Oscar), `US-322` (Estefany).

**Avanzadas:** `US-212` a 95% — BUG-026 cerrado, único bloqueo ADR-007; `US-321` con ML-03 entrenado
y registrado; `US-325` con los tres PRs coordinados; `US-303` con los tres modelos por el mismo
camino; `US-222` con la capa de datos validada contra Postgres real.

`US-221` merece nota: seguía diciendo «PR #106 abierto» cuando se mergeó a las 00:50. Lo reportó
Manuel Serranía. **Es el tipo de deriva que hace que el tablero deje de ser confiable**, y por eso la
reconciliación diaria no es burocracia.

## Registro de bugs

**BUG-018 estaba mal.** La matriz de trazabilidad lo daba por corregido desde el 28-ago, pero el
registro seguía en `open`. El registro es la fuente canónica y no puede ir detrás de la matriz.
Corregido con la evidencia de Andrés.

**Cuatro bugs sin dueño, asignados:**

- **BUG-012** (runbook del pipeline local) — **a mi nombre.** Llevaba días marcado «pendiente (C1)»
  sin persona. Los 7 pasos verificados de Marina viven en un DevLog personal y son el único registro
  que existe. Con BUG-026 cerrado el pipeline ya es reproducible desde fixtures, así que por fin se
  puede escribir completo y verificarlo.
- **BUG-017** y **BUG-019** — **a mi nombre como convocante.** No son defectos de código sino una
  decisión pendiente: se cierran al ratificar ADR-007. Tenerlos sin dueño los hacía parecer trabajo
  técnico de alguien más, cuando lo que falta es una junta.
- **BUG-020** (crítico, 500 en la URL pública) — Christian y Luis, **con seguimiento diario mío hasta
  cerrarlo**. Se pidió estado dos veces sin respuesta; sin seguimiento nombrado se queda igual.

**Tabla normalizada** (V-04c del plan de corrección): ocho filas traían una columna extra heredada
(`ver detalle`) y BUG-025 una de menos. Al normalizar hubo que cuidar los pipes escapados de los
wikilinks — `vault_lint` atrapó uno que se me rompió, que es exactamente para lo que sirve.

## Lo que aprendí del día, y va al guion de la junta

**Tres defectos distintos con la misma causa en 48 horas**, todos por incorporar `cve_mun` al
contrato: la invariante de DEC-007 (230 filas contra 315), BUG-028 (el cero de la izquierda perdido
en el lector de producción) y un test de Estefany que heredaba del fixture la ausencia de la columna
y dejó de comprobar nada.

Ninguno estaba mal escrito. Los tres **asumían algo del entorno en vez de declararlo**. El criterio
que propongo adoptar: cuando un contrato incorpora un campo, se busca activamente todo lo que asumía
su ausencia; y las pruebas construyen su propia precondición en vez de heredarla.

Lo importante para la junta: **las tres las atrapó una guarda, no un usuario.** El sistema funcionó.

## También corregí algo mío

En el plan de corrección del vault afirmé que `vault_lint` no detecta IDs duplicados. **Es falso** —
sí los detecta, y lo comprobé al mergear `main` en la rama del PR #87:
`❌ IDs duplicados (1): ADR-007`. Lo que falló fue dejar una rama tres días sin actualizar: su último
check corrió el 26-ago y el ADR de Héctor nació el 28. La herramienta está bien; el check describía
un repositorio que ya no existía.

Corregí la entrada V-02 y de ahí salió una regla mejor que la que había escrito: **un PR con checks
de más de 24 horas no se mergea sin revalidar.**

## Uso de IA

Claude Code condujo la revisión de los 15 PRs, resolvió cinco conflictos de merge (#124, #127, #131,
#132, #114, #125, #87), diagnosticó BUG-028 y redactó el guion de la junta. Revisé cada resolución
de conflicto antes de empujarla y verifiqué que ninguna referencia se perdiera. No se pegaron datos
reales ni credenciales en los prompts.

Una nota de proceso: en un push le pasé al agente un nombre de rama deducido del título del PR en vez
de leído del PR, y se creó una rama huérfana. Se corrigió y desde entonces el nombre se obtiene con
`gh pr view --json headRefName`. Lo anoto porque el error fue silencioso: el push funcionó, pero
contra la rama equivocada.

## Pendiente

- **Ratificar ADR-007** — desbloquea US-212, DB-04, BUG-017 y BUG-019.
- **BUG-020** — único riesgo vivo para la casilla 6 del ensayo y para el punto de URL pública.
- **DS-07 en `draft` desde la Semana 1** — afecta a D1, el driver de mayor peso. Escalado a Deni.
- Acuerdo Manuel ↔ Monserrat sobre `valor_promedio_driver` (PR #134).
- Ejecutar V-01 a V-05 del plan de corrección del vault.
