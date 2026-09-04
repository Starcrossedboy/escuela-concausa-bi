---
project: "FARO"
date: "2026-09-03"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "opus-5"
session_duration: "sesión de verificación de la auditoría de Marina García del Buey"
touches: ["US-207", "US-215a", "US-215b", "US-412", "US-416", "REQ-004"]
tags: [devlog, ownership, tablero, auditoria, marina]
---

# DevLog — 2026-09-03 — Auditoría de Marina García: 9 de 10 hallazgos reales

→ [[vault/_DevLog/_index|Volver al índice]] · `vault/_Meta/ownership.yml` ·
[[vault/12_Roadmap_Sprints/Execution_Status]]

## Qué se pidió

Marina García del Buey reportó 3 "contradicciones" y 10 hallazgos tras auditar su propio alcance,
`ownership.yml`, el tablero PM y varios documentos de C2. No arregló nada — pidió verificación y
plan de acción.

## Qué se verificó

**Las 3 contradicciones:**
- **C1 (nadie puede editar su propio plan de sprint) — FALSA.** `check_ownership.py:212` agrega
  `persona["plan"]` al alcance permitido de forma incondicional, sin importar si
  `vault/12_Roadmap_Sprints/**` aparece en su `verde`/`amarillo`. El empate que su Agent Context le
  pedía resolver ("manda el archivo") no aplicaba: no había empate, había una vía en el código que
  las listas declarativas no muestran. Aplica a los 21, no solo a ella.
- **C2 (`requirements/celula-2.txt` imposible) — VERDADERA.** Confirmado: el archivo no existe y
  Célula 2 era la única de las 5 sin ninguna entrada de `requirements/` en `ownership.yml`.
- **C3 (US-215a sin dónde vivir) — VERDADERA**, y es consecuencia directa de H3.

**Los 10 hallazgos — 9 verdaderos, verificados uno por uno contra el código y el repo real**, no
solo leídos: H2 (BUG-031 fantasma — no se tocó hoy, queda para quien lo revise), H3
(`06_Quality_Testing/` sin dueño más allá de `Automated/**` y `Bug_Register.md`, confirmado con
`grep`), H4 (US-412/US-416 `in_review` en el tablero pese al commit `5951e37` de cierre en `main`),
H5 (cero coincidencias de "lighthouse" en `.github/` ni `08_CICD_DevOps/`), H6 (`UX_Guidelines.md`
con `source_of_truth: true` y "Principios de diseño" vacío), H7 (`configuracion.env` versionado no
coincide con `.env`/`.env.*` del `.gitignore` ni con el grep de CI), H9 (confirmado, sin US-207 en
su Agent Context), H10 (confirmado, `setup_proyecto.sh` bajo el comentario de Graphify).
**H1 no se tocó**: es correcto que Luis haya editado archivos de Marina el 31-ago —
`ownership.yml` nació el 2-sep, no había regla vigente que violar.

**Matiz importante sobre H7**: el `git ls-files | grep` y el `.gitignore` sí tenían el hueco
reportado, pero **G5 GitLeaks** (`ci.yml`) ya corre como gate separado y escanea **contenido**, no
nombre de archivo — un secreto real en `configuracion.env` ya se habría cachado por ahí. El hueco
era real pero el riesgo práctico era menor de lo que parecía a primera vista.

## Qué se corrigió

- **`ownership.yml`**: `requirements/celula-2.txt` al amarillo de los 4 de C2 (Manuel, Marina,
  Monserrat, Oscar) · `vault/06_Quality_Testing/**` a `comunes` (cubre `_index.md`,
  `Test_Strategy.md`, ambos planes de usabilidad —el de DB05/DB08 y el que le falta crear a Marina
  para DB03/DB04—, `Guion_E2E_Verificacion_4.md`, `Physical_Manual/`, `QA_Logs/`).
- **`Execution_Status.md`**: `US-412` → `done` (DEC-012 ya resuelto en sesión previa, solo faltaba
  escribirlo: 404 estructurado + 200 verificados en vivo el 2-sep). `US-416` se actualiza con la
  evidencia del cierre del 2-sep pero **se queda en `in_review`** — Christian (TL C4) no ha
  ratificado el diseño, condición explícita que la propia fila exige.
- **`.gitignore`**: `*.env` agregado (cualquier archivo que termine en `.env`, no solo el literal) ·
  reordenados `setup_proyecto.sh` y los dos patrones de fixtures a secciones que sí describen lo
  que hacen.
- **`.github/workflows/ci.yml`**: el grep de "Sin secretos versionados" pasa de `(^|/)\.env$` a
  `(^|/)[^/]*\.env$` — mismo hallazgo, verificado con casos reales (`.env.example` sigue sin
  coincidir, `configuracion.env` ya sí).
- **`vault/04_UX_Design/Accessibility.md`**: se corrige la afirmación falsa de un gate de Lighthouse
  en CI que no existe; el umbral pasa de "bloqueante" a "aspiracional, verificar a mano".

## Qué queda para decisión o trabajo posterior (no se tocó)

- **H2** (BUG-031 fantasma en el registro) y **H6** (contenido real de `UX_Guidelines.md`) — quedan
  para quien los revise; no son ownership, son contenido que alguien con criterio de dominio debe
  escribir o corregir.
- **H8** (BUG-012, runbook del pipeline local) — sigue asignado a mí desde el 29-ago. Ya no tiene
  bloqueo real (BUG-026 cerró el que lo detenía); pendiente de sesión dedicada.
- **US-215a** ya tiene dónde vivir (H3 resuelto); falta que Marina la escriba.
- **US-207** en su Agent Context — es `comunes`, se lo dejo a ella (H9).

## Verificado

`vault_lint.py` limpio · `pytest tests/ -q` → 840 passed, 7 skipped · `ruff check .` limpio ·
`generate_pm_dashboard.py` → 91 US, 21 personas, 8 fuentes · `validate_pm_dashboard.py` → TEST-002
válido · `ci.yml` válido como YAML · los 3 escenarios de C2/H3 confirmados uno por uno contra
`check_ownership.py`.

## IDs tocados

`US-207`, `US-215a`, `US-215b`, `US-412`, `US-416`, `REQ-004`

## Próximos pasos

- Mensaje a Marina con el resultado de la verificación (corrección de C1 incluida).
- H8 (runbook BUG-012) como sesión dedicada, ya sin bloqueo.
- H2 y H6 esperan a quien tenga el contexto de dominio para corregirlos.
