---
project: "FARO"
date: "2026-08-31"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — refuerzo del filtro de preguntas del agente (P-13, guard)"
touches: ["US-304a", "BUG-025", "REQ-006"]
tags: [devlog, agente, guardrails, seguridad, intencion]
---

# DevLog — 2026-08-31 — P-13: el filtro de preguntas del agente clasifica por intención

→ [[_DevLog/_index|Volver al índice]] · [[06_Quality_Testing/Bug_Register|BUG-025]]

## Contexto

P-13 (lista de remediación del agente): antes de **conectar el LLM** (`generar_sql`/`redactar_respuesta`,
que llegan con el PR #152, aún **abierto**), el propio plan pide revisar el filtro de preguntas.
`src/agente/guardrails.py::pregunta_en_alcance` clasificaba solo por **tema**: *"borra la tabla de
predicciones"* pasaba por contener la palabra "predicciones". Con el LLM conectado, ese SQL destructivo
sí se generaría y el validador de SQL pasaría a ser la **única** capa real.

Este PR es el **guard** de P-13 (independiente de #152): endurece el filtro de preguntas como
**defensa en profundidad**. El **fix** (cablear el LLM) va en un PR posterior, cuando #152 esté en
`main` (hoy sólo #150 —ejecutor SQL read-only— está mergeado).

## Qué se hizo

- **`pregunta_en_alcance`** ahora aplica dos filtros: (1) TEMA, como antes; (2) **INTENCIÓN**: rechaza
  órdenes de escritura aunque toquen vocabulario de FARO.
  - Verbos destructivos **directos** (borra, elimina, trunca, destruye, drop, delete, truncate, …) →
    rechazo inmediato.
  - Verbos **ambiguos** (actualiza, crea, modifica, inserta, …) → sólo si además nombran un objeto de
    datos (tabla, registro, columna, …), para no atrapar preguntas legítimas.
  - Match por **token exacto**: capta imperativos/infinitivos (cómo se dan las órdenes) sin atrapar
    conjugaciones de lectura ("¿qué escuelas se actualizaron?"). Limitación conocida (documentada en el
    código): el tokenizador no capta acentos → cubre formas sin tilde; lo que se escape lo detiene el
    validador de SQL.
- **NO se tocó** `validar_sql_lectura`/`preparar_sql_seguro`/`aplicar_limit` (guardarrailes de SQL,
  intocables): siguen siendo la barrera final y exhaustivamente probados.
- **Pruebas** (`tests/test_agente_guardrails.py`, +9): órdenes directas rechazadas (incl. el caso de
  P-13), ambiguo+objeto rechazado, y preguntas de lectura legítimas que **no** se rechazan por
  intención. Ajustados `tests/test_agente_endpoint.py` y `tests/test_agente_servicio.py` para que su
  pregunta siga siendo legítima y así **el validador de SQL siga siendo el que corta** el DELETE del
  LLM (su cobertura se preserva), más un test nuevo en cada uno del corte por intención.

## Validación

- `pytest tests/ -q --continue-on-collection-errors` (venv 3.11): **428 passed, 5 skipped**. Los
  4 failed + 14 errors son de Carril A (`great_expectations`/`scikit-learn` ausentes en el venv mínimo),
  **idénticos** a los de antes del cambio → no son regresiones. En CI (deps completas) pasan.
- Superficie del agente aislada: `test_agente_guardrails/endpoint/servicio` → **40 passed**.
- `python _Meta/scripts/vault_lint.py .` → **Vault limpio**.
- Revisión manual: el cambio no filtra SQL en el mensaje al usuario y degrada seguro.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Creados:** `src/agente/guardrails.py` (constantes + helper `_intencion_de_escritura`), este DevLog.
- **Modificados:** `src/agente/guardrails.py::pregunta_en_alcance`, `tests/test_agente_guardrails.py`,
  `tests/test_agente_endpoint.py`, `tests/test_agente_servicio.py`, `_DevLog/_index.md`.
- **Revisión línea por línea:** sí. Sin datos reales ni credenciales en prompts.

## Pendientes / avisos a otros owners

- **PM (Edgar):** este PR es el guard de P-13. El fix (cablear `get_generar_sql`/`get_redactar_respuesta`
  guardado por `ANTHROPIC_API_KEY`, igual que #150 hace con `ejecutar_sql`) requiere **#152 mergeado**.
- **C3 (Andrés):** #152 (`src/agente/llm.py`) sigue **OPEN**; al integrarse, el cableado lo conecta sin
  reescribir tu adaptador.
