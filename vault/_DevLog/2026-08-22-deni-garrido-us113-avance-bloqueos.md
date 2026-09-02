---
project: "FARO"
date: "2026-08-22"
author_human: "Deni Garrido Fragoso"
agent: "ChatGPT"
model: "GPT-5.6 Sol"
type: devlog
session_duration: "sesión distribuida; duración no consolidada"
touches: ["US-113", "REQ-001", "DEC-009", "DB-01", "DB-02", "DB-03", "DB-04", "DB-05", "DB-06", "DB-07", "DB-08", "DB-09", "DB-10"]
tags: [devlog, data-engineering, dbt, gold, cubos, bloqueo]
---

# 2026-08-22 — Deni Garrido · US-113 avance técnico y bloqueos

## Objetivo

Construir vistas materializadas Gold optimizadas para los 10 dashboards, con
banderas explícitas de cobertura para distinguir `SIN_DATO` de valores reales.

## Estado técnico

### Aplicado y commiteado en la rama local US-113

- `cubo_escuela_360` — DB-03.
- `cubo_recomendaciones` — DB-09.
- `cubo_pivot` — DB-08.
- `cubo_comparador_municipio` — DB-04.

La rama local al iniciar este registro está en:

`f43bd55e91982f8b5180ea4ff7abd2ce785c66f3`

### Validado, revisado línea por línea y aprobado; pendiente de DEC-009

- `cubo_completitud`
  - SHA-256 aprobado:
    `710a7d68df54fd0670068aa5355e84679911af0c11f6f83371714f232fb9452b`
- `cubo_matricula`
  - SHA-256 aprobado:
    `81d704c5a92cacc1048bc15466d81b7eba6ffee2bc4c65ea25aa8128fa99d6f0`
- `cubo_riesgo_territorial`
  - SHA-256 aprobado:
    `59b3d2daa59452ad9e0776370bc4148e3cace39b3ffe11ffc7725df081489021`
- `cubo_driver`
  - SHA-256 aprobado:
    `e5b7cc1fa1a2545ad0df48a2eb527a2c630fcfb467f068647ab63c6eff4c5c4a`

Estos patches no se aplican hasta que el contrato canónico en `origin/main`
registre DEC-009 y los granos acordados:

- `cubo_matricula`: municipio × nivel × ciclo.
- `cubo_riesgo_territorial`: municipio × nivel × ciclo.
- `cubo_driver`: driver × municipio × nivel × ciclo.
- `cubo_completitud`: municipio × nivel × driver × ciclo.

## Bloqueos confirmados al 22-ago-2026

### BLOCK A — DEC-009 no está canónico

El gate contra `origin/main` confirmó:

- `Decision_Log.md` todavía no contiene `DEC-009`.
- `Data_Model.md` todavía publica los granos anteriores:
  - matrícula: entidad × municipio × ciclo;
  - riesgo territorial: municipio × ciclo;
  - driver: driver × municipio × ciclo;
  - completitud: municipio × driver × ciclo.

Por gobernanza, los cuatro patches aprobados se mantienen congelados y sin
aplicar hasta que el contrato canónico coincida con la decisión aprobada.

### BLOCK B — DB-10 / cubo_pipeline sin relación canónica

La auditoría encontró metadata `_ingested_at`, `_source` y `_source_url` en
Bronze/Silver y extractores, pero no encontró un modelo/seed/source dbt
canónico que represente metadata versionada de ingesta para materializar
`cubo_pipeline`.

No se inventa una fuente. DB-10 queda bloqueado hasta que exista el contrato
físico/canónico correspondiente o el dueño de arquitectura defina cuál usar.

## Validación ejecutada en los cubos

Los candidatos se validaron en worktrees aislados con Graphify primero,
PostgreSQL efímero y, según correspondía:

- `dbt parse`, `dbt run`, `dbt test`;
- materialización física como `MATERIALIZED VIEW`;
- pruebas de grano y ausencia completa de grupos;
- paridad contra hechos y salidas ML;
- diferenciación explícita entre cero real y `SIN_DATO`;
- segunda ejecución / refresh;
- `pytest`;
- `vault_lint`;
- `git diff --check`;
- Graphify post-cambio.

## Regla para retomar

1. Ejecutar `git fetch origin`.
2. Confirmar DEC-009 en `Decision_Log.md`.
3. Confirmar los cuatro granos en `Data_Model.md`.
4. Aplicar únicamente los patches cuyos SHA-256 coincidan byte por byte con
   los aprobados.
5. Si aparece una relación dbt canónica para metadata de ingesta, revisar el
   contrato antes de construir `cubo_pipeline`.
6. No marcar US-113 como terminada ni abrir PR final mientras estos bloqueos
   permanezcan.

## Estado reportado

US-113: **85% — bloqueada por dependencias canónicas externas**.

`REQ-001` permanece **En progreso**.

## Corrección de criterio posterior

Después de registrar el cierre parcial, se revisó la confirmación escrita de
Diana, owner del Data Model. Diana confirmó explícitamente los cuatro granos con
`nivel` y autorizó a Deni a materializar bajo ese criterio para US-113.

Por lo tanto:

- DEC-009 **ya no se considera bloqueo para materializar en la rama US-113**.
- La publicación de DEC-009 / `Data_Model.md` se conserva como gate antes del
  **merge final** a `main`, no como gate de desarrollo.
- Los cuatro patches aprobados (`cubo_completitud`, `cubo_matricula`,
  `cubo_riesgo_territorial`, `cubo_driver`) se aplicaron con sus SHA-256
  aprobados y fueron revalidados en conjunto.
- El único bloqueo técnico externo restante es DB-10 / `cubo_pipeline`, porque
  todavía no existe una relación dbt canónica y versionada de metadata de ingesta.

Estado actualizado de US-113: **92% — bloqueada únicamente por DB-10 / cubo_pipeline**.
