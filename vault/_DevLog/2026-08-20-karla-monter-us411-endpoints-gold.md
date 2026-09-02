---
project: "FARO"
date: "2026-08-20"
author_human: "Karla Alejandra Monter Benitez"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "2 sesiones — endpoints de lectura sobre Gold (US-411)"
touches: ["US-411", "REQ-004"]
tags: [devlog, celula-4, api, gold, backend]
---

# DevLog — 2026-08-20 — US-411: endpoints de lectura sobre Gold

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/03_Architecture/API_Specification|API_Spec §3.3]]

## Contexto

US-411 pide rutas de lectura parametrizadas sobre Gold (escuelas, municipios, KPIs, series) con
paginación, filtros y ordenamiento. Partía del stub de `mock_data` (US-401); el trabajo fue
conectarlo a `gold.*` real y resolver 3 discrepancias de contrato que surgieron en el camino,
cada una con su propio dueño de decisión.

## Qué se hizo

**1. `/escuelas`, `/municipios`, `/kpis` reales sobre Postgres** (`src/api/db.py` nuevo — motor
SQLAlchemy Core + tablas de `gold.*`). Fórmulas de KPI tomadas literalmente de
`vault/04_UX_Design/Screen_Specs.md` (KPI-02 variación ponderada, KPI-04 escuelas en riesgo vía JOIN a
`gold.predicciones` con umbral 0.6, KPI-05 completitud promedio).

**2. Decisión 1 (Christian Ruiz, Tech Lead C4):** `indice_riesgo`/`driver_dominante` en
`EscuelaOut`/`EscuelaDetalleOut` pasan a `Optional` + `tiene_prediccion: bool` (DEC-008 también
agrega `es_estimado_por_grupo`, `None` mientras la columna no exista en `gold.predicciones` —
pendiente de Diana/Héctor, fuera de mi alcance). `/escuelas` y `/escuelas/{cct}` quedan reales con
`LEFT JOIN` a `gold.predicciones`/`gold.recomendaciones`.

**3. Decisión 2 (Christian Ruiz):** patrón *dependency override* para que la suite rápida del
contrato corra sin Postgres. Se extrajo `src/api/repositorio_gold.py` (nuevo): `Protocol
RepositorioGold` + `RepositorioGoldPostgres` (mismo SQL que antes vivía en `gold.py`, solo movido
detrás de la interfaz) + `get_repositorio_gold()` inyectado con `Depends(...)` en las 5 rutas de
`src/api/v1/gold.py`. `tests/fixtures_gold.py` (nuevo) define `RepositorioGoldFake` con datos
sintéticos en memoria; `tests/test_api_contract.py` hace
`app.dependency_overrides[get_repositorio_gold] = RepositorioGoldFake` en el fixture `client`.
**Nada de SQLite** (acordado explícitamente): no maneja el esquema `gold` igual que Postgres y
daría falsos verdes. Las pruebas de integración contra Postgres real quedan para US-422 (Eloisa
González Rubio), con Postgres efímero como *service* de CI.

**4. Decisión 3 (mía, avisada a C2/C3 — ver Bloqueantes):**
- `/series` declarado **fuera de alcance** de US-411 en `API_Specification.md` §3.3: la única
  serie de tiempo real documentada (KPI-15/AC-002.5, matrícula por `cct×ciclo`) es de **US-212,
  Célula 2**, y se consume como cubo Superset (`gold.cubo_escuela_360`), no como endpoint REST;
  hoy `fact_escuela_ciclo` solo materializa 2 ciclos (no hay serie real que servir); ningún
  consumidor la referencia.
- **Ordenamiento** agregado a `/escuelas` y `/municipios`: `order_by` como `Literal` de Pydantic
  (whitelist explícita — `422` fuera de lista, nunca texto libre hacia SQL) + `order` (`asc`/
  `desc`). `SIN_DATO` (`None`) siempre al final (`NULLS LAST` en Postgres, mismo criterio a mano
  en el fake).

**5. Contrato y OpenAPI:** `vault/03_Architecture/API_Specification.md` §3.3 y §4 sincronizados con cada
decisión; `api/openapi.v1.json` regenerado (`python scripts/export_openapi.py`).

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-sonnet-5.
- **Archivos creados:** `src/api/db.py`, `src/api/repositorio_gold.py`, `tests/fixtures_gold.py`,
  este DevLog.
- **Modificados:** `src/api/config.py`, `src/api/schemas.py`, `src/api/v1/gold.py`,
  `tests/test_api_contract.py`, `vault/03_Architecture/API_Specification.md`, `api/openapi.v1.json`.
- **Decisiones autónomas del agente:** forma exacta de la interfaz `RepositorioGold` (qué métodos,
  qué devuelven como `dict` plano); whitelist de campos ordenables (`ESCUELAS_ORDENABLES`/
  `MUNICIPIOS_ORDENABLES`) limitada a los campos que ya devuelven `EscuelaOut`/`MunicipioOut`;
  convención `NULLS LAST` para `SIN_DATO` al ordenar (documentada, no forzada por nadie más);
  redacción de la nota de `/series` fuera de alcance en el contrato. Las decisiones de **fondo**
  (qué hacer con `/series` y si agregar ordenamiento) se le presentaron a Karla como opciones con
  evidencia (grep de `PLAN_MAESTRO.md`, `fact_escuela_ciclo.sql`, ausencia de consumidores) y ella
  eligió.
- **Correcciones manuales:** ninguna sobre el código generado en esta sesión; Karla revisó cada
  decisión antes de que se implementara (Decisión 2 y 3 confirmadas explícitamente antes de tocar
  código).
- **Prompt inicial:** continuación de sesión previa vía `US411_CONTEXTO_TRABAJO.md` (documento
  scratch, no es artefacto del vault — se borra antes del PR).

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Tests agregados/actualizados: `tests/test_api_contract.py` pasó de 18 a 23 casos (+5 de
  ordenamiento); `tests/fixtures_gold.py` nuevo. Suite completa `pytest tests/ -q` (sin
  `test_publicar_gold.py`, requiere Postgres real): **163 passed, 4 skipped**.
- [x] DevLog enlaza a los IDs afectados (US-411, REQ-004)

## Bloqueantes / avisos a otros owners
- **Pendiente enviar a C2/C3:** aviso de la Decisión 3 (`/series` fuera de alcance +
  ordenamiento en `/escuelas`/`/municipios`) — se manda junto con la apertura del PR, no en esta
  sesión.
- **Diana Álvarez / Héctor Morales (C1/C3):** `es_estimado_por_grupo` sigue sin existir como
  columna en `gold.predicciones` — `EscuelaDetalleOut` la devuelve `None` explícito mientras tanto.
- **Diana Álvarez (C1), ya reportado, no corregido (fuera de mi alcance):**
  `dbt/models/gold/dim_municipio.sql` y `fact_escuela_ciclo.sql` usan `source()` en vez de
  `ref()`, rompiendo el orden real de dependencias de dbt.
- **Eloisa González Rubio (US-422):** la interfaz `RepositorioGold` ya está lista para que la
  suite de integración contra Postgres real la implemente vía `RepositorioGoldPostgres`.

## Próximos pasos
- Borrar `US411_CONTEXTO_TRABAJO.md`.
- Abrir el PR (rama `feat/karla-benitez-us411-endpoints-gold`) con el aviso de Decisión 3 a C2/C3.
- US-413 (admin protegido) y US-414 (docs OpenAPI + colección) son historias separadas de S5, no
  parte de este cierre.
