---
project: "FARO"
date: "2026-09-01"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — item 7 PROMPT-B: ruff.toml deja el gate de lint en verde (B008 idioma FastAPI)"
touches: ["US-523b", "REQ-007", "REQ-004"]
tags: [devlog, ci, lint, ruff, calidad, carril-b]
---

# DevLog — 2026-09-01 — ruff.toml: gate de lint en verde sin mutilar la API (item 7)

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Item 7 de la remediación (PROMPT-B §6.7). `main` no tiene `ruff.toml`: `ruff check .`
reporta **58 hallazgos preexistentes** y CI los tolera con `|| true`
(`.github/workflows/ci.yml:82`). El **PR #165 (US-523b)** quita ese `|| true` **sin
limpiar nada** → con 58 errores, endurecer el gate pondría **rojo** `main`. De los 58,
**21 son B008** (`function-call-in-default-argument`) dentro de `src/api/`: son
`Depends()` / `Query()` de FastAPI en argumentos por defecto —**el idioma del framework,
no deuda**—. Sin config, quien endurezca el gate obliga a mutilar los endpoints.

Decisión del PO (consultada, no asumida): **"gate verde ya, política global"** — el
`ruff.toml` no solo exime B008 en `src/api`, sino que deja `ruff check .` en **0** para
que #165 sea viable de inmediato. Eso implica fijar la política de lint también sobre
código de otras células (deuda preexistente que no es mía y que **no puedo editar**,
§4). Lo hago exonerando **por carpeta**, con cada exoneración documentada y con dueño.

## Qué se hizo

Un solo archivo nuevo: **`ruff.toml`** en la raíz (mi territorio, §4). Diseño:

- **No override de `select`**: se hereda el ruleset default de ruff, que es *exactamente*
  lo que CI corre hoy. Probé fijar un `select` explícito y **activaba reglas más estrictas
  que el default** (E402/E731/E741/B007/B905…) metiendo hallazgos nuevos → descartado.
  Igual con `target-version = "py311"`: activa UP017 (`timezone.utc`→`datetime.UTC`) y
  suma ~29 hallazgos de modernización en código preexistente → tampoco se fija. Solo se
  exonera; nunca se amplía el ruleset.
- **`[lint.per-file-ignores]`** (58 = 26+13+9+3+3+2+2):
  - `src/api/**` → `B008` (**permanente**, idioma FastAPI) + `DTZ005`/`I001`/`RUF100`
    (deuda mía de fase 2; no las "arreglo" para no cambiar comportamiento —los `DTZ005`
    son timestamps de respuesta en `main.py:66,88`— ni ampliar un PR de solo-config).
  - `dags/**` → `I001`,`DTZ001` (Carril A/Airflow) · `_Meta/**` →
    `I001`,`EXE001`,`DTZ011`,`SIM115` · `scripts/**` → `I001`,`EXE001` ·
    `src/frontend/**` → `I001`,`UP045` · `src/ingesta/**` → `I001`,`RUF013` (Carril A) ·
    `tests/**` → `I001`.
- **B008 sigue activo fuera de `src/api`** (no hay `ignore` global): si alguien mete una
  llamada en un argumento por defecto fuera de la API, el gate lo atrapa.

## Validación (local)

- `ruff check .` (modo **estricto**, como quedará #165 sin `|| true`) →
  **`All checks passed!`** (exit 0). Con esto #165 se vuelve viable sin romper `main`.
- `ruff check . --isolated` (sin mi config) → sigue en **58** (la baseline queda intacta:
  mi archivo solo exonera, no altera el ruleset base).
- `ruff check . --output-format=github || true` (modo CI de hoy) → **sin anotaciones**.
- `python3 _Meta/scripts/vault_lint.py .` → **Vault limpio**;
  `validate_pm_dashboard.py .` → válido (TEST-002).
- `pytest tests/ -q` (suite completa, venv 3.11) → **453 passed, 4 failed, 5 skipped,
  13 errors**. Los **4 failed** (todos `tests/test_validacion_sesnsp.py`) y los **13
  errors** de colección (`test_entrenar_ml*`, `test_extractor_*`, `test_validacion_*`,
  `test_riesgo`, `test_evaluar`, `test_target_hibrido`, `test_publicar_gold`) son **el
  mismo fallo ambiental del venv** (`great_expectations…row_conditions`) y **todos de
  Carril A** — ninguno de mi territorio, y un `ruff.toml` no puede alterar el runtime de
  pytest. **Mi territorio** (`-k "api or semantic or kpis or agente or auth"`) → **338
  passed, 0 failed**.

## Qué necesito del Carril A

- **Nada** para cerrar este item. La **fase 2** (limpiar la deuda exonerada en `dags/`,
  `src/ingesta/`, `tests/fixtures/`, etc.) es de cada célula; queda listada en `ruff.toml`
  y aquí para que la retomen cuando toque.

## Hallazgos fuera de la lista

- **CI instala `ruff` sin fijar versión** (`pip install ruff`, `ci.yml:75`) — *leído*. Si
  un release futuro cambia el ruleset default, los 58 pueden moverse y el gate podría
  ponerse rojo solo. Endurecerlo (pin de versión o `select` explícito **tras** limpiar la
  deuda) es fase 2; lo anoto, no lo toco en este PR (es de #165 / quien endurezca el gate).
- **`DTZ001` en 6 DAGs** (Airflow) y **`SIM115` en `_Meta/scripts/vault_lint.py:118`** —
  *deducido de ruff*: pueden ser **latentes** (zona horaria del schedule / fuga de
  descriptor), no solo estilo. Marcados "REVISAR" en `ruff.toml` para su dueño.

## Seguridad / alcance

- Solo un archivo de config en mi territorio (`ruff.toml` · `.github/**` en §4). **Cero
  ediciones de código** (mío o ajeno) → sin cambios de comportamiento, sin mover números
  de Gold.
- Sin credenciales ni contenido de `.env`; **local-first, nada promovido a producción**.
