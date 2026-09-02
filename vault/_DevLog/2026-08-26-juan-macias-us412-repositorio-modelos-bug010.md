---
project: "FARO"
date: "2026-08-26"
author_human: "Juan Carlos Macías Mayen"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "~2h"
touches: ["US-412", "BUG-010", "REQ-004", "REQ-003"]
tags: [devlog]
---

# DevLog — 2026-08-26 — US-412: `RepositorioModelos` real, cierra BUG-010

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo
- Investigando US-412 encontré que ya existía **BUG-010** (`vault/06_Quality_Testing/Bug_Register.md`,
  Héctor Morales, 24-ago): `/predicciones/*` seguía leyendo `src/api/mock_data.py`, y
  `PrediccionOut.cluster` no tenía productor (ML-03/US-321 sin entregar). El plan de sprint
  original ("cargar los 3 modelos desde MLflow") estaba desactualizado: `gold.predicciones` y
  `gold.recomendaciones` ya están pobladas y verificadas (US-313), así que el swap correcto es
  leer esas tablas, no invocar MLflow por request.
- `src/api/repositorio_modelos.py` (nuevo): `RepositorioModelos` (Protocol) +
  `RepositorioModelosPostgres`, mismo patrón `Depends` que `RepositorioGold` (US-411). Lee
  `gold.predicciones` (`modelo='ML-01'`, `grano='escuela'` — DEC-010) `JOIN` `gold.recomendaciones`.
- `src/api/db.py`: agregada la columna `grano` (post-DEC-010) que le faltaba a la tabla
  `predicciones`.
- `src/api/schemas.py`: `PrediccionOut.cluster` pasa de `StrictInt` a `StrictInt | None = None`
  -- mismo criterio SIN_DATO que `EscuelaOut.indice_riesgo`. **Cambia el contrato público**,
  pendiente de avisar a C2/C3 (regla de oro de `API_Specification.md`).
- `src/api/v1/predicciones.py`: `prediccion`/`prediccion_batch` ahora usan
  `Depends(get_repositorio_modelos)`; ya no importan `mock_data` para esas dos rutas.
  `explicacion` queda igual (SHAP no tiene fuente en Gold; fuera de alcance de BUG-010).
- `src/api/mock_data.py`: `cluster` fabricado (`int(cve_mun[:2]) % 4`) corregido a `None`.
- `tests/fixtures_modelos.py` (nuevo): `RepositorioModelosFake`, mismo patrón que
  `fixtures_gold.py`. `tests/test_api_contract.py` lo inyecta vía `dependency_overrides`; 3
  pruebas nuevas (200 con cluster=None, 404 sin fila, batch omite CCT sin fila).
  `vault/03_Architecture/API_Specification.md` y `api/openapi.v1.json` actualizados.
  `vault/06_Quality_Testing/Bug_Register.md`: BUG-010 → `fixed`, con nota de resolución.
- Suite completa: 360 passed, 5 skipped. `vault_lint.py` limpio.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code (Sonnet 5)
- **Archivos creados/modificados:**
  - `src/api/repositorio_modelos.py` (nuevo)
  - `tests/fixtures_modelos.py` (nuevo)
  - `src/api/db.py`, `src/api/schemas.py`, `src/api/v1/predicciones.py`, `src/api/mock_data.py`
  - `tests/test_api_contract.py`
  - `vault/03_Architecture/API_Specification.md`, `api/openapi.v1.json`
  - `vault/06_Quality_Testing/Bug_Register.md`
- **Decisiones autónomas del agente:**
  - `cluster` opcional en vez de una bandera `tiene_cluster`: ML-03 no cubre a ninguna escuela
    hoy (a diferencia de `tiene_prediccion`, que sí varía por escuela), así que una bandera
    constante sería ruido. Documentado en la resolución de BUG-010.
  - `explicacion` (SHAP) se deja fuera de alcance: no tiene fuente en Gold y BUG-010 no la cubre
    explícitamente: cambiar su contrato (`contribuciones` no-opcional) sería una decisión propia,
    no la de este bug.
- **Correcciones manuales:** ninguna aún (revisión línea por línea pendiente antes del PR).
- **Prompt inicial:** continuación de la sesión de US-415; el usuario confirmó la resolución de
  `cluster` (opcional, mismo patrón SIN_DATO de `EscuelaOut`) antes de tocar el contrato público.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Tests agregados/actualizados (`tests/fixtures_modelos.py`, 3 casos nuevos en
      `test_api_contract.py`)
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes
- Ninguno de los 3 modelos está registrado en el MLflow local; no bloquea este swap porque ya no
  se invoca MLflow en el request path (se lee `gold.predicciones`/`gold.recomendaciones`).
- `RepositorioModelosPostgres` no se probó contra Postgres real con datos reales: mi Postgres
  local no tiene el esquema `gold` materializado (no corrí dbt end-to-end). La prueba de
  integración real es US-422 (Eloisa González Rubio).

## Próximos pasos
- Avisar a Manuel Serranía (C2) y Andrés González Habib / Héctor Morales (C3) del cambio de forma
  en `PrediccionOut.cluster` -- regla de oro del contrato.
- Actualizar `vault/02_Requirements/Traceability_Matrix.md` (fila REQ-004) -- coordinar con Edgar
  Coronel (PM), zona amarilla de mi Agent Context.
- Abrir PR (US-415 + US-412 + BUG-010) con Karla Monter como revisora.
