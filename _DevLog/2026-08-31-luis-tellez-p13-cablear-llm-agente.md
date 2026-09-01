---
project: "FARO"
date: "2026-08-31"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — fix de P-13: cableado del LLM del agente (tras resolver #152)"
touches: ["US-304a", "BUG-025", "REQ-006"]
tags: [devlog, agente, llm, wiring, seguridad]
---

# DevLog — 2026-08-31 — P-13 (fix): cablear el LLM del agente por configuración

→ [[_DevLog/_index|Volver al índice]] · [[06_Quality_Testing/Bug_Register|BUG-025]]

## Contexto

P-13 tenía dos mitades: el **guard** (endurecer el filtro de preguntas por intención, PR #176, ya en
`main`) y el **fix** (conectar el LLM que hoy hace degradar al agente con "El contexto de FARO no está
disponible temporalmente."). El fix estaba **bloqueado** por el adaptador de C3 (`src/agente/llm.py`,
PR #152 de Andrés), que llegó a `main` en esta sesión. Con el guard y el adaptador ya integrados, este
DevLog documenta el fix.

## Qué se hizo

- **Cableado condicional del LLM** en `src/api/app.py`: si hay `ANTHROPIC_API_KEY`, la app sobreescribe
  el seam de inyección del agente (`get_generar_sql` → `generar_sql_con_llm`, `get_redactar_respuesta`
  → `redactar_respuesta_con_llm`). Las firmas del adaptador — `(prompt, pregunta)` y `(pregunta, filas)`
  — **casan exactas** con lo que espera `procesar_consulta`, así que el wiring es directo (sin
  adaptadores intermedios), **igual patrón** que #150 usa para `get_ejecutar_sql` con el DSN read-only.
- **Gobierno por configuración**: `anthropic_api_key: str = ""` en `src/api/config.py`. Vacío ⇒ el LLM
  **no** se cablea: el seam conserva sus defaults seguros ("no configurado"), CI/local no llaman a
  Anthropic y el agente degrada. La clave la provisiona C5 en Secret Manager; el adaptador lee esa
  misma variable y la config no secreta (`AGENTE_MODELO`/`AGENTE_MAX_TOKENS`/`AGENTE_TIMEOUT_S`) del
  entorno.
- **`.env.example`**: documenta `ANTHROPIC_API_KEY` (secreto, vacío) y los 3 parámetros no secretos.
- **Pruebas** (`tests/test_agente_wiring_llm.py`, 2): con clave ⇒ ambas etapas cableadas a las
  funciones reales; sin clave ⇒ el seam no se toca. No se **invoca** el LLM (solo se comprueba qué
  callable queda), así que la suite sigue offline.

## Defensa en profundidad (por qué conectar el LLM es seguro ahora)

Con el LLM conectado, ninguna capa queda sola:

1. **Filtro de intención** de la pregunta (guard P-13, #176): corta órdenes de escritura antes de
   llamar al LLM.
2. **`preparar_sql_seguro`** (guardarraíl de SQL, intocable §9): valida solo-lectura + `LIMIT` sobre lo
   que devuelva el LLM.
3. **Ejecutor read-only** (#150): rol PostgreSQL solo-SELECT sobre `gold.*`, `SET TRANSACTION READ ONLY`.

## Validación

- Foco del agente + ejecutor + wiring: `test_agente_wiring_llm/endpoint/servicio/guardrails` +
  `test_ejecutor_gold` → **46 passed** (venv 3.11).
- Suite completa: `pytest tests/ -q --continue-on-collection-errors` → **437 passed, 5 skipped**. Los
  4 failed + 14 errors son de Carril A (`great_expectations`/`scikit-learn` ausentes en el venv
  mínimo), **idénticos** a antes del cambio → no son regresiones. En CI (deps completas) pasan.
- `python _Meta/scripts/vault_lint.py .` → **Vault limpio**.
- Revisión manual: sin `ANTHROPIC_API_KEY`, el endpoint degrada sin filtrar detalle (comportamiento
  BUG-025 preservado); el wiring no ejecuta el LLM al construir la app.

## Otros movimientos de la sesión

- **Resolución del conflicto de #152**: la rama de Andrés chocaba con `main` solo en
  `_DevLog/_index.md` (índice de bitácoras). Con autorización, integré `origin/main` en su rama
  conservando **todas** las filas (merge limpio verificado con `git merge-tree`), sin tocar su código;
  Edgar la aprobó y mergeó. Igual actualización aplicada a la rama del guard #176.

## Pendientes / avisos a otros owners

- **C5 (yo, en despliegue):** para activar el agente en prod hay que provisionar `ANTHROPIC_API_KEY`
  **y** `DATABASE_URL_READ_ONLY` en Secret Manager. Con solo la clave del LLM, `generar_sql` funciona
  pero el ejecutor sigue degradando (correcto y seguro). No promover a prod hasta autorización del PM.
- **PM (Edgar):** este PR cierra P-13 a nivel estructural (guard + fix). La respuesta real del LLM en la
  URL viva depende de que C5 cargue los secretos.
