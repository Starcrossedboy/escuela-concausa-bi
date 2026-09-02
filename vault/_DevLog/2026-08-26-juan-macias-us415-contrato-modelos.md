---
project: "FARO"
date: "2026-08-26"
author_human: "Juan Carlos Macías Mayen"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "~2h"
touches: ["US-415", "REQ-004"]
tags: [devlog]
---

# DevLog — 2026-08-26 — US-415: contrato de datos API ↔ modelos

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo
- Onboarding completo del entorno local (Homebrew, GitHub CLI, Python 3.11 via `.venv`,
  `docker compose up -d`, `.env` con claves generadas por `scripts/generate-keys.py` -- las de
  `.env.example` tenían placeholders sin reemplazar y un mismatch de password entre
  `POSTGRES_PASSWORD` y `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` que hacía fallar `airflow-init`).
- Implementado `src/api/schemas_ml.py` (US-415): contrato interno entre `gold.features_escuela`
  y las salidas crudas de ML-01/02/03, insumo de `PrediccionOut` (US-412). Reutiliza
  `FeaturesEscuela` de `src/modelos/contrato.py` (no lo duplica).
- Documentado en `vault/03_Architecture/API_Specification.md` §7 (nuevo).
- 11 pruebas nuevas en `tests/test_schemas_ml.py`. Suite completa: 358 passed, 5 skipped.
  `vault_lint.py` limpio. `ruff check` limpio.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code (Sonnet 5)
- **Archivos creados/modificados:**
  - `src/api/schemas_ml.py` (nuevo)
  - `tests/test_schemas_ml.py` (nuevo)
  - `vault/03_Architecture/API_Specification.md` (§7 agregado, `last_reviewed` actualizado)
  - `.env` (local, no versionado -- claves regeneradas)
- **Decisiones autónomas del agente:**
  - `driver_dominante` en `ML02Salida` como `Literal["D1".."D6"]` (no `str` libre), siguiendo el
    mismo principio de whitelisting que `order_by` en `repositorio_gold.py` (Decisión 3 de US-411).
  - Alineación `cct`/`id_ciclo` entre las 3 salidas forzada con `model_validator`, en vez de
    confiar en que el llamador las pase coherentes.
  - Documenté explícitamente en API_Specification.md §7 que ningún modelo está registrado hoy en
    el MLflow local y que ML-03 no tiene aún código de entrenamiento (US-321 sin entregar) --
    para no bloquear US-412, que se construirá contra un fake inyectable.
- **Correcciones manuales:** ninguna aún (revisión línea por línea pendiente antes del PR).
- **Prompt inicial:** onboarding + ejecución de US-415 y US-412 según
  `vault/12_Roadmap_Sprints/Sprints/4-juan-carlos-macias-mayen.md` y
  `vault/09_AI_Governance/Agent_Contexts/juan-macias-agent-context.md`.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Tests agregados/actualizados (`tests/test_schemas_ml.py`, 11 casos)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- Ninguno de los 3 modelos (ML-01/02/03) está registrado en el MLflow local todavía; ML-03
  (US-321, Estefany Hernández) no tiene código de entrenamiento propio aún. No bloquea US-415;
  sí condiciona a que US-412 se construya con un fake inyectable (patrón `RepositorioGold`) hasta
  que los registros existan.

## Próximos pasos
- Pendiente: actualizar `vault/02_Requirements/Traceability_Matrix.md` (fila REQ-004) -- coordinar con
  Edgar Coronel (PM) antes de tocarla, zona amarilla de mi Agent Context.
- Abrir PR de US-415 con Karla Monter como revisora.
- Continuar con US-412 (endpoints de inferencia ML) sobre este contrato.
