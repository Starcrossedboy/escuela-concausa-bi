---
project: "FARO"
date: "2026-09-04"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión de cola de PRs: acciones del equipo, decisiones (DEC-006, FARO Web) y revisión de PR #215/#216/#217"
tags: [devlog, ownership, execution-status, pm, bug-046, bug-047]
---

# DevLog — 2026-09-04 — Cierre de US-212/US-411, hueco de `requirements.txt` y colisión BUG-046

→ [[vault/_DevLog/_index|Volver al índice]] · `vault/_Meta/ownership.yml` ·
[[vault/12_Roadmap_Sprints/Execution_Status]]

## Qué se pidió

Revisar los pendientes que Marina García y Christian Ruiz reportaron el 2026-09-04, generar un
plan de acción para lo que solo el PM puede cerrar, y verificar los PRs de la cola (#215 Manuel,
#216 Diana, #217 Luis Téllez) antes de aprobarlos.

## Qué se verificó y se corrigió

**`ownership.yml`**: `requirements.txt` de la raíz no tenía dueño en ningún lado — el padrón solo
cubría `requirements/**` (la carpeta). Es el único archivo que instala el job `quality` de
`ci.yml`; sin él, nadie podía agregar `streamlit` y las 3 pruebas de frontend seguían saltándose
en silencio. Agregado a `comunes`. Confirmado con `check_ownership.py` que esto era, en efecto, lo
único que bloqueaba al PR #215 de Manuel.

**`Execution_Status.md`** — barrido completo, no solo los 2 casos reportados:
- `US-212`: `in_review` → `done`. Solicitud escrita por Marina en `Traceability_Matrix.md` tras el
  PR #211 (no lo pudo tocar ella, es verde exclusivo del PM). ADR-007 implementado punta a punta,
  AC-002.4 verificado por partida doble (Marina y Héctor, mismas cifras).
- `US-214a`: `planned` → `in_progress`. 2 de 4 rutas de drill-down listas (PR #211); las otras 2
  esperan el filtro `cct` de Manuel en DB-06/DB-09.
- `US-411`: `in_review` → `done`. Encontré esta solicitud yo mismo revisando DevLogs recientes
  (Karla, 2026-09-03) — ninguno de los dos reportes del equipo la mencionaba. Su texto propuesto
  dejaba el estado en `in_review` porque faltaba el redeploy y la reverificación; ambos ya
  ocurrieron el mismo día (Luis Téllez redeploy, Christian reverificación en vivo:
  `/kpis`=6,704,229), así que cierra completo, no parcial.
- Verificado y descartado como no-acción: `ADRs/**`/`.env.example`/`dags/**`/`common_alerting/**`
  en `ownership.yml` (ya cubiertos desde el 09-03) y la fila `US-004` que Luis Téllez marcó como
  malformada el 09-02 (ya no lo está, columnas correctas).

**Colisión BUG-046**: el PR #215 (Manuel, dashboards) y el PR #217 (Luis Téllez, OAuth) registraron
el mismo ID en paralelo, ambos partiendo del mismo commit base donde BUG-045 era el máximo en
`main`. El de Luis Téllez es `critical` (bloquea todo login real en producción) y merge primero;
renumeré el de Manuel a **BUG-047** directamente en `dev/manuel-serrania` (push mecánico, sin tocar
la sustancia del fix) para no dejar un ID duplicado en el registro.

## Decisiones ratificadas por el PO en esta sesión

- **DEC-006 no se reabre.** Se usa el ranking de mayor riesgo + driver dominante para la demo, no
  un conteo (que da 0 con el umbral actual — verificado por Marina, no es un defecto).
- **FARO Web se contenoriza**, no demo local — Manuel y Luis Téllez lo toman como siguiente paso.

## Verificado

`vault_lint.py` limpio · `validate_pm_dashboard.py` válido · `pytest tests/ -q` → 884 passed, 7
skipped · gate de ownership simulado contra el PR #215 con este fix aplicado → pasa limpio ·
tablero PM regenerado: 69.1% → 70.3% (44 → 46 de 91 `done`).

## IDs tocados

`US-212`, `US-214a`, `US-411`, `REQ-002`, `REQ-004`, `BUG-046`, `BUG-047`

## Próximos pasos

- Mergear PR #218 (este), luego sincronizar `dev/manuel-serrania` con `main` para que su gate pase.
- Aprobar y mergear #217 (Luis Téllez) y #216 (Diana) — ambos ya en verde.
- Pedir a Manuel que corrija 2 imprecisiones de conteo de pruebas en su PR (33→2 en un archivo,
  21 failed/12 sin colectar → 0/0 en ambiente limpio) — no bloqueante, calidad del registro.
