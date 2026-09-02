---
project: "FARO"
date: "2026-08-22"
author_human: "Manuel Alejandro Serrania Reinada"
agent: "OpenCode"
model: "ox-alpha"
type: handoff
touches: ["US-203", "REQ-002", "AC-002.1", "AC-002.2", "AC-002.3", "AC-002.5", "KPI-01", "KPI-02", "KPI-03", "KPI-04", "TEST"]
tags: [devlog, handoff, bi, superset, playwright, e2e, celula-2]
---

# Handoff — 2026-08-22 (tarde) — OpenCode · verificación E2E de US-203

## Handoff — 2026-08-22 — OpenCode (ox-alpha)

- **Current objective:** verificar con Playwright el reporte de Manuel ("US-203 no funciona
  correctamente"), diagnosticar causa raíz y comparar el estado real contra los AC de REQ-002.
- **Current branch:** `feat/manuel-serrania-us203-dashboards-insignia` (commit `2fa629c`, tree limpio,
  **rama aún sin push ni PR**).
- **Latest graph status:** grafo 2026-08-07, sin regenerar (pendiente desde el handoff anterior).
- **Relevant Graphify queries:** ninguna útil para `superset/` (fuera del grafo, igual que antes).
- **Files changed:** ninguno en esta sesión (solo lectura/pruebas). Evidencias en
  `/tmp/opencode/evidencia/`: `db01-filtro-primaria-v3.png`, `db02-post-restart.png`,
  `db-0*-estado.png`.
- **IDs touched:** US-203 · REQ-002 (AC-002.1/.2/.3/.5) — sin cambios de código.
- **Decisions made:** ninguna de código; se decidió NO tocar la instancia (no borrar el dashboard
  residual `TEST filtros`) sin confirmación de Manuel.

### Resultados E2E (Playwright headless, login por UI)

| Verificación | Resultado |
|---|---|
| Login UI | ✅ |
| DB-01 | ✅ 9/9 charts con datos (KPI-01=5,837 · KPI-02=-117.8% · KPI-05=65% · serie · tabla · 2 pies · drivers) |
| DB-02 | ✅ 7/7 charts con datos (7 · 31.8% · 0.48 · 5,837 · coroplético con leyenda · scatter con puntos · ranking con N/A por R2) |
| Barra filtros nativos | ✅ montada en ambos (VERTICAL) |
| Filtro nivel=PRIMARIA en DB-01 | ✅ KPI-01 5,837→1,657 · KPI-02 -117.8%→-14.8% (idéntico al handoff previo) |
| HTTP ≥400 en sesión | ✅ ninguno (solo 404 cosmético de `service-worker.js`) |
| pytest suite completa | ✅ 256 passed, 4 skipped (`test_semantic_db01_db02.py`: 47) |
| vault_lint | ✅ Vault limpio |

### Diagnóstico del reporte "no funciona"

1. **Colgado transitorio reproducido una vez:** a las ~07:39 DB-02 quedó con sus 7 charts en estado
   "Waiting on faro_escuela_concausa_db" indefinidamente (captura `db-02-estado.png`) mientras DB-01
   cargaba al instante. El frontend ni siquiera disparaba `POST /api/v1/chart/data`.
2. **No reproduce tras `docker restart faro-superset`:** arranque en frío → 6/7 charts con datos en
   ~2 s (el restante es canvas-only, verificado pintado por WebGL) y captura `db02-post-restart.png`
   muestra el tablero completo y correcto.
3. **Hipótesis principal:** caché en memoria corrupta/obsoleta de la sesión de sync nocturna
   (Superset stock sin Redis usa caché por worker en memoria; el restart la limpia). Las SQL de DB-02
   corren en <100 ms directo en Postgres, descartando problema de datos/conexión.

### Gaps reales encontrados vs AC-002.2 (cableado declarativo, requieren fix en YAML + re-sync)

1. **DB-02 no tiene filtro "Entidad federativa"** (solo Ciclo + Nivel). DB-01 sí tiene 3.
2. **El coroplético ignora el filtro Ciclo:** `filtros_globales[0].datasets` de DB-02 no incluye
   `db02_coropletico`, pese a que ese SQL expone `id_ciclo` en su grano. Tiles y scatter responden al
   ciclo; el mapa no → inconsistencia visible en la demo.
3. **En DB-01, el filtro Entidad solo alcanza a `db01_cubo_matricula`:** los SQL
   `db01_distribucion_escuelas` y `db01_driver_dominante` no exponen `cve_ent`, así que los pies
   KPI-08/KPI-09 y el gráfico de drivers no reaccionan a ese filtro (limitación estructural del SQL,
   decisión de diseño a ratificar o corregir).

### Higiene pre-PR detectada

- `SESION-RESUMEN-US203.md` sigue en raíz (borrar antes del PR, ya estaba marcado como riesgo).
- Dashboard residual **"TEST filtros" (id=3)**, no publicado, quedó en la instancia de Superset:
  eliminarlo manualmente desde la UI antes de la demo (no se tocó por política anti-DELETE).
- La rama no está pusheada; el PR hacia `main` sigue pendiente de aprobación del PM (DEC-003).

- **Open questions:**
  - ¿Se corrigen los 3 gaps de filtros (YAML + `sync_semantic_layer.py`) antes del PR o después?
  - ¿Quién elimina el dashboard "TEST filtros" y cuándo?
  - ¿Documentar el workaround de colgado transitorio (restart del contenedor) en `superset/README.md`?
- **Risks:** el colgado transitorio puede reaparecer tras un sync mientras no haya backend de caché
  externo (Redis); mitigación documental a corto plazo.
- **Tests executed:** ver tabla E2E + `pytest tests/ -q` (256/4) + `vault_lint.py` ✅.
- **Next recommended action:**
  1. Manuel valida visualmente ambos tableros (hard-refresh).
  2. Decidir sobre los 3 gaps de AC-002.2 y aplicar fixes en YAML → re-sync → re-test E2E.
  3. Borrar `SESION-RESUMEN-US203.md`, push y PR con aprobación del PM.

> Entradas canónicas previas: [[vault/_DevLog/2026-08-21-manuel-serrania-us203-tableros-db01-db02]] ·
> [[vault/_DevLog/2026-08-22-handoff-us203-tableros-superset]]
