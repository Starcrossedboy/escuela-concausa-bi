---
project: "FARO"
date: "2026-08-22"
author_human: "Manuel Alejandro Serrania Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
type: handoff
touches: ["US-203", "REQ-002", "KPI-01", "KPI-02", "KPI-03", "KPI-04", "KPI-05", "KPI-07", "KPI-08", "KPI-09", "KPI-10", "DEC-005", "DEC-008"]
tags: [devlog, handoff, bi, superset, dashboards, celula-2]
---

# Handoff — 2026-08-22 — OpenCode (opencode/big-pickle)

## Handoff — 2026-08-22 — OpenCode

- **Current objective:** US-203 completa y verificada: tableros DB-01/DB-02 en Superset 6.1 con capa
  semántica declarativa, mock ML, GeoJSON municipal, filtros nativos funcionales y verificación E2E
  con Playwright. Cambios LOCALES (commiteados en esta rama; sin push ni PR a la fecha del handoff).
- **Current branch:** `feat/manuel-serrania-us203-dashboards-insignia`
- **Latest graph status:** grafo del 2026-08-07 (`graphify-out/`); NO regenerado en esta sesión —
  los archivos nuevos de `superset/` no están en el grafo. Ejecutar `graphify update` al integrar.
- **Relevant Graphify queries:** ninguna útil para esta historia (el grafo no cubre `superset/`);
  el contexto vino de `vault/_DevLog/`, `vault/04_UX_Design/Screen_Specs.md`, `vault/03_Architecture/Data_Model.md`
  y el código fuente dentro del contenedor (`docker exec faro-superset ...`) + GitHub tag 6.1.0.
- **Files changed:**
  - Nuevos: `superset/semantic/{db01_cubo_matricula,db01_distribucion_escuelas,db01_driver_dominante,
    db02_cubo_riesgo_territorial,db02_coropletico,db02_puntos_escuela}.sql`,
    `superset/semantic/metrics_db01_db02.yaml`, `superset/dashboards/{db01_ejecutivo,db02_mapa_riesgo}.yaml`,
    `superset/mock/gold_ml_outputs_mock.sql`, `superset/assets/geojson/municipios_scope.geojson`,
    `superset/{generar_geojson,cargar_geojson}_municipios.py`, `tests/test_semantic_db01_db02.py`,
    `SESION-RESUMEN-US203.md` (TEMPORAL en raíz — eliminar antes del merge).
  - Modificados: `superset/sync_semantic_layer.py`, `superset/README.md`, `docker/superset.Dockerfile`,
    `vault/_DevLog/_index.md`.
- **IDs touched:** US-203 · REQ-002 · KPI-01/02/03/04/05/07/08/09/10 · DEC-005 (completitud drivers) ·
  DEC-008 (componentes aditivos) · R1/R2/R3/R5.
- **Decisions made:**
  1. Datasets como SQL virtual autocontenido (contrato de US-113 para C1), igual que US-211a.
  2. Mock ML determinístico por hash(CCT), marcado MOCK-US203, idempotente y no destructivo.
  3. GeoJSON espejo comunitario INEGI/CONABIO 2023 (MIT), simplificado a 608 KB.
  4. Razones guardadas puras + formato d3 con `%` (un único mapa `FORMATO_D3`); prohibido `*100` en SQL.
  5. Dashboards se sincronizan vía importación v1 (bundle ZIP multipart) porque el PUT REST no llena
     `dashboard_slices`; charts y métricas sí por REST PUT directo.
  6. `filter_bar_orientation: "VERTICAL"` en mayúsculas (enum del frontend) — causa de la barra fantasma.
- **Open questions:**
  - ¿Quién ejecuta `graphify update` tras el merge? (grafo desactualizado desde 2026-08-07)
  - Revisión de C5 al fix del Dockerfile (uv pip vs pip) — señalado en DevLog, pendiente su visto bueno.
  - KPI-02 global (-117.8%) es real del mock; ¿se queda así hasta que lleguen datos de C3?
- **Risks:**
  - `SESION-RESUMEN-US203.md` temporal en raíz puede colarse al main si nadie lo borra antes del merge.
  - El bundle de importación depende de UUIDs estables derivados de nombre; renombrar un chart/dataset
    duplicaría objetos (renombrar = borrar manual + re-sync).
  - Rate limit 50 req/s de esta imagen: corridas muy paralelas podrían recibir 429 (ya hay reintento).
  - Los N/A del ranking DB-02 son correctos (R2) pero pueden leerse como error sin contexto.
- **Tests executed:**
  - `pytest tests/test_semantic_db01_db02.py -q` → 47 passed
  - `python -m pytest -q` → 256 passed, 4 skipped
  - `ruff check superset/ tests/test_semantic_db01_db02.py` → limpio (44 errores preexistentes fuera
    de alcance en `vault/_Meta/scripts/`, `dags/`, `src/`)
  - `python vault/_Meta/scripts/vault_lint.py .` → ✅ Vault limpio
  - Playwright E2E: 16/16 charts renderizan con datos; filtro `nivel=Primaria` cambia KPI-01
    5,837→1,657 y KPI-02 -117.8%→-14.8%; capturas en `/tmp/opencode/evidencia/`
  - Sync idempotente verificado (segunda corrida crea 0 objetos)
- **Next recommended action:**
  1. Manuel revisa visualmente ambos tableros en `127.0.0.1:8088` (hard-refresh Ctrl+Shift+R).
  2. Aprobación del PM → abrir PR hacia `main` (recuerda borrar `SESION-RESUMEN-US203.md`).
  3. Tras merge: `graphify update` y notificar a Marina que US-212 está desbloqueada.

> Entrada canónica de la sesión: [[vault/_DevLog/2026-08-21-manuel-serrania-us203-tableros-db01-db02]]
