---
project: "FARO"
date: "2026-09-03"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-5"
session_duration: "sesión larga: revisión de 6 PRs + BUG-042"
touches: ["BUG-042", "US-004", "REQ-007", "TEST-034"]
tags: [devlog, tablero, execution-status, bug042, ownership]
---

# DevLog — 2026-09-03 — Cobertura completa de Execution_Status.md (BUG-042)

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/12_Roadmap_Sprints/Execution_Status]] ·
[[vault/06_Quality_Testing/Bug_Register]]

## Qué se pidió

Oscar Quiroz reportó que su tabla de sprint estaba desactualizada; al verificar el hallazgo se
destapó algo mayor: `Execution_Status.md` — la fuente de verdad del tablero PM — solo tenía fila
para 67 de las 91 historias. Las 24 restantes se contaban como `planned` por default del
generador, fuera cierto o no.

## Qué se encontró

- **24 historias sin fila.** Auditadas una por una contra PRs mergeados en `main`: **10 tenían
  evidencia real** (algunas terminadas, otras con trabajo entregado y solo bloqueadas por algo
  ajeno al autor). Las otras 14 sí eran `planned` de verdad — auditoría, no suposición.
- **Una fila mal etiquetada.** `US-206` cargaba la evidencia de `US-205` (repunteo de la capa
  semántica, PR #134) — hallazgo de Manuel Serranía, confirmado contra el DevLog que la propia
  fila enlazaba. Se reetiquetó a `US-205` y se dio de alta `US-206` con su evidencia real (PR
  #193, embebido de dashboards).
- **BUG-042**: `build_snapshot()` en `generate_pm_dashboard.py` completaba con
  `state.get("status", "planned")` — ausencia de fila y "no ha arrancado" eran indistinguibles.
  Mismo patrón que BUG-040: un valor por defecto que parece dato es peor que un error.
- De paso, dos huecos reales en `ownership.yml` que bloqueaban a terceros sin culpa suya:
  `vault/03_Architecture/ADRs/**` y `.env.example` no eran de nadie (hallazgo de Christian Ruiz,
  US-402); y `dags/**`/`common_alerting/**` no estaban en el alcance de Edgar Jiménez pese a que
  ya había tocado ambos para US-524b antes de que el gate existiera.

## Qué se corrigió

- `vault/12_Roadmap_Sprints/Execution_Status.md`: 24 filas nuevas + reetiquetado de `US-206`.
  Cobertura **91/91**.
- `vault/_Meta/scripts/generate_pm_dashboard.py`: `build_snapshot()` ya no asume `planned`; falla
  con la lista completa de historias sin fila si alguna vuelve a faltar.
- `vault/_Meta/ownership.yml`: `ADRs/**` y `.env.example` a `comunes`; `common_alerting/**` al
  verde de `edgar-jimenez`; `dags/**` a su amarillo y a `criticos` con Diana Álvarez como
  revisora — resuelve el hueco sin abrir `dags/**` a cualquiera.
- `tests/test_generate_pm_dashboard.py`: 2 casos nuevos (`TEST-034`) — cobertura real de las 91,
  y que inyectar una historia sin fila truene mencionando `BUG-042`.

## Verificado

`vault_lint.py` limpio · `pytest tests/ -q` → 810 passed, 6 skipped · `ruff check .` limpio ·
`generate_pm_dashboard.py` → 91 US, 21 personas, 8 fuentes · `validate_pm_dashboard.py` → TEST-002
válido · los 4 escenarios de `ownership.yml` (Christian/ADR-004, Christian/.env.example, Edgar
Jiménez/dags, Edgar Jiménez/common_alerting) confirmados uno por uno contra `check_ownership.py`.

## IDs tocados

`BUG-042` · `US-004` · `REQ-007` · `TEST-034`

## Próximos pasos

Ninguno de esta clase pendiente. Los 4 registros nuevos (`US-321`, `US-223`, `US-224`, `US-524b`)
quedan `in_progress` con la razón exacta de su bloqueo escrita en la propia fila — no un estado
sin explicación.
