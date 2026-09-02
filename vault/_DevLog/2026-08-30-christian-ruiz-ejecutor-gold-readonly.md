---
project: "FARO"
date: "2026-08-30"
author_human: "Christian Imanol Ruiz Hurtado"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — ejecutor SQL read-only del agente (US-404 / BUG-025)"
touches: ["US-404", "BUG-025", "REQ-004", "REQ-006", "ADR-004"]
tags: [devlog, celula-4, api, seguridad, agente, sql, read-only]
---

# DevLog — 2026-08-30 — Ejecutor SQL read-only sobre Gold (agente)

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt|ADR-004 §Hardening]] · [[vault/06_Quality_Testing/Bug_Register|BUG-025]]

## Contexto

Con US-404 y BUG-025 ya en `main`, se implementa la última pieza C4 del agente: la colaboración
`ejecutar_sql` del seam (`src/api/v1/agente.py`) — ejecutar contra Gold el SQL que genera el LLM,
**de solo lectura**. Atiende el comentario de revisión (C4/Christian) con la corrección de respetar el
patrón `Settings` (minúsculas, sin `os.getenv` suelto). Cambio de seguridad → regla 7.

## Qué se hizo

- **`src/api/ejecutor_gold.py`** (`ejecutar_sql_read_only`) con defensa en profundidad:
  1. rol PostgreSQL con solo `SELECT` sobre `gold.*` (DSN `DATABASE_URL_READ_ONLY`, distinto de la
     conexión general — mínimo privilegio);
  2. `SET TRANSACTION READ ONLY` por conexión;
  3. `statement_timeout` configurable (`AGENTE_SQL_TIMEOUT_MS`, 30 s);
  4. revalidación con `validar_sql_lectura()` antes de tocar la BD (redundante, a propósito).
  Engine cacheado (`lru_cache`); errores de BD → `RuntimeError` sin filtrar DSN/SQL.
- **Config** (`config.py`): `database_url_read_only` y `agente_sql_timeout_ms` por el patrón
  `Settings` — **no** `os.getenv` suelto (corrección de la revisión).
- **Wiring** (`app.py`): `app.dependency_overrides[get_ejecutar_sql] = ejecutar_sql_read_only` **solo
  si** `DATABASE_URL_READ_ONLY` está definido; sin él, el agente usa el default seguro del seam y
  CI/local no tocan Postgres.
- **Pruebas** (`tests/test_ejecutor_gold.py`, 4): rechazo de escritura sin tocar BD, RuntimeError sin
  configuración, happy-path con engine falso (mapeo a dicts + SET TRANSACTION READ ONLY), y cableado
  condicional del override. Suite total 632 passed / 5 skipped.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-4-8.
- **Archivos creados:** `src/api/ejecutor_gold.py`, `tests/test_ejecutor_gold.py`, este DevLog.
- **Modificados:** `src/api/config.py`, `src/api/app.py`, `.env.example`,
  `vault/03_Architecture/ADRs/ADR-004-autenticacion-oauth2-jwt.md`, `vault/_DevLog/_index.md`.
- **Adaptaciones sobre el snippet de la revisión:** (1) config por `Settings`, no `os.getenv`; (2)
  engine cacheado en vez de crear uno por llamada; (3) defensa en profundidad con
  `validar_sql_lectura`; (4) wiring guardado por presencia del DSN (CI/local seguros); (5) timeout
  configurable.
- **Revisión manual:** verificado que no se filtra DSN/SQL en errores; ruff limpio.

## Seguridad / calidad
- [x] Mínimo privilegio (rol solo SELECT), SET TRANSACTION READ ONLY y statement_timeout
- [x] Defensa en profundidad (revalidación) + errores sin fuga de DSN/SQL
- [x] Sin `os.getenv` suelto; config por `Settings`; sin secretos en código
- [x] Pruebas nuevas (`tests/test_ejecutor_gold.py`, 4); suite 632 passed / 5 skipped

## Bloqueantes / avisos a otros owners
- **C5 (Luis):** crear el rol `faro_agente_readonly` (`GRANT SELECT ON ALL TABLES IN SCHEMA gold` +
  `ALTER DEFAULT PRIVILEGES`), el secreto en Secret Manager y `--set-secrets=DATABASE_URL_READ_ONLY=...`
  en Cloud Run. Sin eso el ejecutor no se cablea (agente degrada seguro).
- **C3 (Andrés):** decisión BLOCK-003 (Anthropic / `claude-sonnet-5`, `anthropic>=0.116` en
  `requirements/celula-3.txt`, vars `ANTHROPIC_API_KEY`/`AGENTE_MODELO`/`AGENTE_MAX_TOKENS`/
  `AGENTE_TIMEOUT_S`) es de su LLM (`generar_sql`/`redactar_respuesta`); el seam ya lo acepta por
  `dependency_overrides`. No es artefacto de C4.
- **Eloisa (US-422):** la ejecución real contra Postgres (rol read-only) se prueba en integración con
  Postgres efímero — este PR solo trae unitarias.
- **Regla 7:** cambio de seguridad → revisión humana explícita.
