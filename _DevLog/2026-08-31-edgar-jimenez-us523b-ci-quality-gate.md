---
project: "FARO"
date: "2026-08-31"
author_human: "Edgar Ulises Jiménez López"
agent: "Claude Code (reconstrucción documental)"
model: "claude-opus-4-8"
session_duration: "activación del quality gate de lint en CI (US-523b) — DevLog reconstruido el 2026-09-01"
touches: ["US-523b", "REQ-007", "REQ-004"]
tags: [devlog, cicd, ci, quality-gate, ruff, US-523b]
---

# DevLog — 2026-08-31 — Edgar Jiménez (quality gate de lint en CI · US-523b)

→ [[_DevLog/_index|Volver al índice]] · [[02_Requirements/Traceability_Matrix|Matriz de trazabilidad]]

**Historia:** US-523b · **PR:** #165 · **Sesión:** activación del gate de lint en el pipeline de CI.

> **Nota de reconstrucción (2026-09-01).** Este DevLog fue reconstruido por Claude Code
> durante el saneamiento de PRs pendientes (Carril A), a partir del *diff* real de la rama
> `feat/edgar-lopez-us523b-quality-gate-ci` y del cuerpo del PR #165. La autoría humana original
> del cambio es de Edgar Ulises Jiménez López. Se documenta el **mecanismo real** verificado
> empíricamente, que **difiere** de lo que afirmaba el cuerpo del PR (ver §"Precisión").

## Qué se hizo
- En `.github/workflows/ci.yml`, el paso **Ruff** deja de tolerar fallos: se quita el `|| true`.
  - Antes: `run: ruff check . --output-format=github || true`  → el lint **nunca** ponía rojo el CI.
  - Ahora: `run: ruff check . --output-format=github`  → un error de lint **bloquea** el merge.
- Limpiezas cosméticas menores en el paso G6 (pip-audit): se retiran emojis del texto de log y
  se normalizan espacios. Sin cambios de lógica en ese paso.

## Mecanismo real (cómo se activa sin poner rojo `main`)
El gate es viable **porque `ruff.toml` ya vive en `main`** (commit `ffaeb55`, trabajo de C5 /
Luis Téllez — ver [[_DevLog/2026-09-01-luis-tellez-ruff-toml-gate-lint|DevLog del ruff.toml]]).
Ese archivo usa `[lint.per-file-ignores]` para **exonerar los 58 hallazgos preexistentes** por
carpeta (`src/api/**`, `dags/**`, `_Meta/**`, `scripts/**`, `src/frontend/**`, `src/ingesta/**`,
`tests/**`), sin mutilar la API con `# noqa` dispersos.

Verificación empírica (2026-09-01, sobre `main` con el merge de esta rama):
- `ruff check .`            → **0 errores**  (con la config del repo)
- `ruff check . --isolated` → **58 errores** (sin la config: los preexistentes)

Es decir: **la config exonera lo viejo; el gate exige que lo nuevo entre limpio.** Ese es
exactamente el comportamiento buscado para US-523b.

## Precisión sobre el cuerpo del PR
El cuerpo del PR #165 describía un "modo incremental" que solo lintaría archivos cambiados.
**El diff no implementa tal lógica**: el paso sigue corriendo `ruff check .` **global** sobre todo
el repo. Lo que hace viable el gate no es un modo incremental, sino las `per-file-ignores` de
`ruff.toml`. Este DevLog documenta el comportamiento real, no el descrito.

## Hallazgo abierto (para el orden de liberación)
Al ser un gate **global**, cualquier `.py` **nuevo** debe pasar `ruff check .`. Dos PRs en cola
introducen loaders nuevos con errores **no exonerados** (sus carpetas están cubiertas, pero los
códigos específicos no):
- **#151** `src/ingesta/cargar_bronze_conagua_real.py`: `F401` (import sin usar · autofix),
  `S110` (try-except-pass) y `BLE001` (except ciego).
- **#163** `src/ingesta/cargar_bronze_cct_real.py`: `B009` ×2 (`getattr` con constante · autofix).

**Implicación de orden:** si este PR (#165) se libera **antes** de sanear #151/#163, esos merges
—o cualquier PR posterior— pondrán rojo el CI. Debe resolverse a nivel de PO/TL: limpiar esos 5
hallazgos en los loaders **antes o junto con** la activación del gate. Es cambio de **CI/CD →
requiere revisión humana explícita** (regla 7 del vault).

## Próximos pasos
- Revisión humana del PO (Edgar Coronel) por tratarse de cambio de CI/CD.
- Coordinar con C1 (Diana / Deni) la limpieza de lint de #151 y #163 antes de que el gate rija.
