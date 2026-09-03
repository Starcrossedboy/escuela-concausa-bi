---
project: "FARO"
date: "2026-09-02"
author_human: "Juan Carlos Macías Mayen"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "~2h"
touches: ["US-412", "US-416", "BUG-020", "REQ-004"]
tags: [devlog, cierre, api]
---

# DevLog — 2026-09-02 — Cierre de US-412 y US-416

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

Sesión para dejar **US-412** y **US-416** listas para `done`: verificación en vivo, la última
pieza de código de US-416 y el paquete de evidencia DoF/DoD.

### 1. Verificación en producción (BUG-020 ya está curado)

BUG-020 lo curó la Célula 5 en **US-505 Fase 2** (PR #144/#146). Verificado en vivo contra
`https://faro-api-526490367142.us-central1.run.app` (mismo resultado en el otro dominio):

```
GET  /api/v1/health                   → 200
GET  /api/v1/escuelas                 → 200 (25 escuelas reales)
GET  /api/v1/predicciones/09DPR0001A  → 404 estructurado {"error":"not_found","request_id":"req_4436df0e"}
POST /api/v1/predicciones/batch       → 200 {"items":[],"total":0,"page":1,"size":100}
```

Las dos rutas de US-412 **responden bien en el despliegue** (`ErrorOut` estructurado, nunca 500).
El 404 / lista vacía es porque `gold.predicciones` está **vacía en prod**: falta que ML-01
publique ahí (US-313 / Héctor / Carril A), no es entregable de C4. El `openapi.json` de prod
coincide con `api/openapi.v1.json` de `main` para todo `/predicciones/*`.

### 2. US-416 — última pieza de código: degradar a 503, no a 500

`src/api/repositorio_modelos.py` · `RepositorioModelosPostgres._con_timeout` capturaba solo
`OperationalError` (timeout). Un `ProgrammingError` por esquema/tabla `gold.*` ausente en el
despliegue —caso real mientras la publicación de ML no haya corrido contra esa base— se escapaba
al handler genérico de `src/api/app.py` y se volvía un **500**.

- Ahora captura cualquier `SQLAlchemyError`, **loguea la excepción concreta** (`_logger.warning`)
  y la traduce a `RepositorioModelosNoDisponible` → `v1/predicciones.py` ya la mapea a **503
  `service_unavailable`** uniforme. `OperationalError` sigue cubierto (es subclase).
- Cierra el criterio del PM del 26-ago sobre US-416: "un modelo no responde" incluye "el esquema
  no existe" → degradación `SIN_DATO`/503 explícita, nunca 500 crudo ni valor inventado.
- Cambio acotado: import + docstring + 4 líneas. No toca la lógica de consulta ni el cache.

### 3. Test de regresión

`tests/test_repositorio_modelos.py` (nuevo, unitario, sin Postgres): `Engine` falso cuyo
`begin()` entrega una conexión que revienta al ejecutar. Casos: `ProgrammingError` y
`OperationalError` → ambos `RepositorioModelosNoDisponible` (unitario y batch); la excepción
cruda queda como `__cause__`, nunca se propaga; `listar_predicciones([])` cortocircuita.
4 pruebas, verdes.

### 4. Documentación de contrato

`vault/03_Architecture/API_Specification.md` §3.4 y §5: la ruta responde **404 estructurado**
cuando no hay fila y **503** cuando Gold no está disponible (timeout **o** esquema ausente),
nunca 500. Nota de despliegue: hoy todo CCT devuelve 404 hasta que corra US-313.

### 5. Evidencia de cierre

- `vault/02_Requirements/Traceability_Matrix.md`: fila de evidencia incremental fechada para
  `REQ-004 · US-412, US-416` (mi fila; el PM consolida).
- `vault/06_Quality_Testing/Bug_Register.md`: nota fechada bajo BUG-020 (verificado en vivo, no
  reproduce; recomendación a Christian/Luis de moverlo a `fixed`→`closed`). No cambio el `status`.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude Code / claude-sonnet-5
- **Archivos creados/modificados:**
  - `src/api/repositorio_modelos.py` (captura `SQLAlchemyError` → 503; logger de módulo)
  - `tests/test_repositorio_modelos.py` (nuevo, 4 pruebas)
  - `vault/03_Architecture/API_Specification.md` (§3.4, §5)
  - `vault/02_Requirements/Traceability_Matrix.md` (fila de evidencia incremental)
  - `vault/06_Quality_Testing/Bug_Register.md` (nota bajo BUG-020)
  - `vault/_DevLog/2026-09-02-juan-macias-cierre-us412-us416.md` (este) + `_index.md`
- **Decisiones autónomas del agente:** ampliar la captura a `SQLAlchemyError` (no solo a
  `OperationalError` + `ProgrammingError`) por ser el supertipo que cubre también
  `InterfaceError`/`DBAPIError`; logueo con `warning`, no `exception`, porque no es un bug del
  servicio sino un estado esperado del despliegue.
- **Correcciones manuales:** —
- **Prompt inicial:** onboarding con los 5 documentos de gobernanza + plan de 7 días; petición
  de planear y ejecutar el cierre de US-412 y US-416.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Test de regresión agregado (`tests/test_repositorio_modelos.py`)
- [x] DevLog enlaza a los IDs afectados (US-412, US-416, BUG-020, REQ-004)
- [x] `pytest tests/ -q` → **778 passed, 5 skipped**
- [x] `ruff check src/api tests/test_repositorio_modelos.py` → limpio

## Hallazgos (para sus dueños, no tocados aquí)
- **`api/openapi.v1.json` está desactualizado en `main`**: `python scripts/export_openapi.py`
  produce diff sin que yo tocara rutas ni esquemas — vienen de BUG-017/019 (`variacion_matricula`
  ±1.0, Diana) y BUG-035 (`poblacion` `int|None`, Luis) ya mergeados. `test_api_contract` no lo
  caza porque solo compara nombres de rutas/esquemas, no campos. Necesita su propio PR y
  coordinación con C1/C5. **No incluido en este PR.**

## Bloqueantes / decisiones pendientes (cuerpo del PR)
- **@Edgar (PM):** (a) fallo de criterio **DEC-012** para US-412 — ¿404 estructurado con
  `gold.predicciones` vacía en prod cumple "la ruta responde en el despliegue" → `done`, o
  espera a US-313?  (b) al mergear, voltear US-412/US-416 a `done` en `Execution_Status.md` y
  reconciliar `Bug_Register`/matriz.  (c) corregir en el dashboard `github_user`
  (`juanmmayen98` → `juanmmayen98-pixel`) y el conteo de PRs #95/#101.
- **@Christian (TL C4):** ratificar el diseño de US-416 (cache TTL por fila, `SET LOCAL
  statement_timeout`, 503) + el endurecimiento a `SQLAlchemyError`; confirmar que el E2E con
  Postgres real es US-422.

## Próximos pasos
- Abrir el PR desde `dev/juan-macias` con estos cambios.
- Pasar a Marina la ficha de contrato de `/predicciones/*` para US-207.
