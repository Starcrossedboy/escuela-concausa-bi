---
project: "FARO"
date: "2026-08-28"
author_human: "Héctor Rafael Morales Marbán"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "30min"
touches: ["ADR-007", "DEC-006", "BUG-017", "US-212", "REQ-003"]
tags: [devlog, celula-3, adr, revision]
---

# DevLog — 2026-08-28 — Marina entra a ADR-007, y DEC-006 refuerza la propuesta

→ [[vault/_DevLog/_index|Volver al índice]]

## Lo que pidió Marina, y por qué tenía razón

Marina García pidió entrar como ratificadora de ADR-007. Verifiqué su argumento contra el texto y es
correcto: mi rechazo de la alternativa B dice literalmente *"un tablero que lea Gold directo —que es
justo lo que hace Superset— seguiría mezclando"*.

Usé a su área como razón para descartar una opción y no la senté en la mesa. **Eso es un defecto de
mi artefacto, no una omisión de cortesía**, y así quedó escrito en el ADR: quien sostiene un
argumento tiene que poder discutirlo.

El costo asimétrico que ella señala también es real y ya está a la vista en el documento: si se
ratifica fracción, `DEC-006` y el umbral 0.6 siguen válidos y Célula 2 no toca nada; si no, hay que
rehacer §5.1 del contrato de DB-03/DB-04.

## Lo que encontré al verificarlo

Al buscar `DEC-006` para citarla correctamente apareció algo que fortalece la propuesta más que todo
mi análisis de correlaciones. La decisión, ratificada el 13 de agosto por Manuel Serranía, dice:

> "escuela en riesgo" = `indice_riesgo ≥ 0.6` ↔ **pérdida de ~5 % de matrícula**

Ese "~5 %" es una fracción. **El umbral que Célula 2 ya usa en sus tableros sólo significa algo si el
target lo es.** Con diferencia absoluta, `0.6` no corresponde a ninguna pérdida porcentual concreta:
corresponde a una cantidad de alumnos distinta en cada escuela.

O sea que ratificar fracción **no es una decisión nueva** — hace explícito lo que DEC-006 ya supuso
al definirse en agosto. La alternativa A (recalibrar sobre alumnos absolutos) obligaría a **reabrir
DEC-006**, no sólo a mover las anclas de la sigmoide. Eso cambia el peso de la discusión.

## Lo que no cambié

El `status` sigue en `proposed`. Agregar a quien faltaba y encontrar un argumento a favor no ratifica
nada; eso le toca a la mesa.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos modificados:** `vault/03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula.md`
- **Decisiones autónomas del agente:**
  - Registrar en el ADR **por qué** faltaba Marina, en vez de sólo añadir el nombre.
  - Agregar `DEC-006` a `traces_up` y a las consecuencias: la decisión ya presuponía fracción.
  - Dejar `proposed` intacto.
- **Correcciones manuales:** revisión línea por línea.

## Pendiente

1. **Ratificar ADR-007.** Ahora con Célula 2 en la mesa.
2. **BUG-020** sigue abierto y es lo que amenaza la casilla 6 del ensayo, no los tableros.
