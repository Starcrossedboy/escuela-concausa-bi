---
project: "FARO"
date: "2026-08-29"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
session_duration: "3.5h"
touches: ["US-205", "US-113", "US-211a", "US-211b", "US-213", "DOC-CUBESPEC-DB0508", "REQ-002"]
tags: [devlog]
---

# DevLog — 2026-08-29 — US-205: repunteo de la capa semántica a `gold.cubo_*` + re-escala DB-05

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

- **Repunteo US-205/US-113:** los **13 datasets virtuales** de `superset/semantic/` dejaron de
  agregar `gold.fact_escuela_ciclo` y pasan a **passthrough/enrich 1:1 de los cubos físicos C1**
  (`gold.cubo_matricula`, `gold.cubo_riesgo_territorial`, `gold.cubo_escuela_360`,
  `gold.cubo_comparador_municipio`, `gold.cubo_driver`, `gold.cubo_pivot`,
  `gold.cubo_recomendaciones`) + `gold.geo_municipio`/`gold.dim_driver` (enrich) +
  `gold.predicciones` (db09, único LEFT JOIN que el cubo de recomendaciones no resuelve).
- **Re-escala DB-05 (decisión C2 aprobada en US-205):** `db05_cubo_driver` pasa de analizar el
  driver observado (KPI-19 propuesto, fuera de v1) al **driver dominante de ML-02 (KPI-07
  ratificado)**, con denominadores reales del cubo (`escuelas_con_recomendacion`,
  `escuelas_sin_recomendacion`, `escuelas_driver`, `total_escuelas`,
  `cobertura_recomendacion`). La agregación a `cve_ent × id_ciclo` del KPI-07 en DB-01
  (`db01_driver_dominante`) ahora **reagrega `gold.cubo_driver`** preservando SIN_DATO como
  etiqueta. DB-08 se conserva observado (KPI-20 intacto).
- **`metrics_db05_db08.yaml` reescrito (sección DB-05):** métricas nuevas, `formato: largo`,
  `dimension_obligatoria_en_agregacion: id_driver`, `grano_canonico_actual` +
  `cambio_de_grano_solicitado_a: "Resuelto en US-205…"`, KPI-19 eliminado de propuestos.
  Nombres/aliases del resto de los YAML intactos (regla dura).
- **`04_UX_Design/Cube_Specs_DB05_DB08.md` → v1.1:** frontmatter (+US-205), §2.1/§2.2/§3.1/§3.2/
  §3.3/§3.6/§5/§5.1/§6/§7/§8.1/§8.3 actualizados al re-scope.
- **Tests:** los 4 tests semánticos (`test_semantic_db0*.py`) reescritos al contrato del
  repunteo (lectura de cubos físicos, sin fact, sin unpivot manual, SIN_DATO literal, umbral
  R3 por YAML) y **nuevo guard** `tests/test_semantic_repunteo_cubos.py` (exactamente 13 SQL,
  nadie lee `gold.fact_*`, allowlist de fuentes, datasets con `cubo_canonico_futuro` consumen
  ese cubo, toda métrica usa solo columnas expuestas por su dataset).
- **Revisión de regresión de las US de Manuel tras el repunteo (pedido del PM):** verificación
  cruzada YAML↔SQL de los 5 `metrics_db*.yaml` contra los 13 datasets → se detectó y corrigió un
  **bug real introducido por el repunteo**: `db09_cubo_recomendaciones` no re-exportaba
  `prioridad`, columna que consume la métrica `recomendaciones_prioridad_alta` (KPI-11) y el
  chart por `[prioridad]` de `db09_recomendaciones.yaml`. El cubo C1 sí la trae; se añadió
  `cr.prioridad` al passthrough + test de cierre + guarda sistémica. Documentación US-202/211a
  actualizada al repunteo (`superset/README.md`, `superset/semantic/README.md`) y matriz de
  trazabilidad (conteos y descripciones de los 5 tests semánticos). `test_kpis_us221` (catálogo
  US-201, 6 casos) sigue en verde.[^1]

[^1]: Pendientes que NO son de esta sesión y quedan documentados: **BUG-027** (sql_ref de
  `metrics_kpis_base_us221.yaml` apunta a `sql/` que no existe; re-mapeo pendiente, follow-up
  US-221/Oscar) y el stash "US-221 followup WIP + RETOMAR (ref Manuel)".

## 🤖 Sesión de IA
- **Agente / modelo:** OpenCode / opencode/big-pickle
- **Archivos creados/modificados:**
  - `superset/semantic/db0*.sql` (13 reescritos: db01_cubo_matricula, db01_distribucion_escuelas,
    db01_driver_dominante, db02_cubo_riesgo_territorial, db02_coropletico, db02_puntos_escuela,
    db03_cubo_escuela_360, db04_cubo_comparador_municipio, db05_cubo_driver, db06_cubo_predicciones,
    db06_predicciones_escuela, db08_cubo_pivot, db09_cubo_recomendaciones)
  - `superset/semantic/metrics_db05_db08.yaml`
  - `04_UX_Design/Cube_Specs_DB05_DB08.md` (v1.1)
  - `tests/test_semantic_db01_db02.py`, `tests/test_semantic_db03_db04.py`,
    `tests/test_semantic_db05_db08.py`, `tests/test_semantic_db06_db09.py`
  - `tests/test_semantic_repunteo_cubos.py` (nuevo)
  - `superset/README.md`, `superset/semantic/README.md` (actualizados al repunteo)
  - `02_Requirements/Traceability_Matrix.md` (conteos/descripciones de tests semánticos)
- **Decisiones autónomas del agente:** el nombre del test `test_db04_agrupa_al_grano_declaro_en_el_cubo`
  quedó con typo menor (`declaro` → `declarado`, sin reescalar en esta sesión).
- **Correcciones manuales:** ninguna en esta sesión (los tres fixes de verificación —alias `c.`
  en el regex, umbral YAML como float, fuente del umbral en db02_coropletico— los hizo el agente).
- **Prompt inicial:** "What did we do so far?" → continuar el plan US-205 de la sesión anterior.

## Seguridad / calidad
- [x] Sin secretos hardcodeados
- [x] Tests agregados/actualizados: `test_semantic_repunteo_cubos.py` (nuevo equipo, no TEST-###)
- [x] DevLog enlaza a los IDs afectados
- [x] Verificación: `pytest tests/test_semantic_db*.py tests/test_semantic_repunteo_cubos.py`
  → **209 passed** (47+27+53+48+34; adentro del scope: los 5 archivos están en verde; fuera de
  scope, `tests/test_cache_predicciones.py` y `tests/test_validacion_sinaica.py` fallan en COLLECT
  por `cachetools` ausente en el venv — preexistente, ajeno a US-205). `test_kpis_us221` ↑
  en verde (6/6) y `test_db07_calidad_cobertura` (7/7, US-222). `ruff check tests/` limpio.
  `python3 _Meta/scripts/vault_lint.py .` → "Vault limpio".

## Actualización post-rebase (mismo día, PR #134)
Rebase de `feat/manuel-serrania-us205-repunteo-cubos` sobre la `main` que avanzó con **#125**
(DB-07/US-222, Oscar), **#114** (dashboards DB-05/08/US-213, Monserrat) y **#128** (ADR-007, docs):

- **`db05_analisis_driver.yaml` re-mapeado al re-scope KPI-07** (6 tabs × 6 charts): los 4 nombres
  viejos (`valor_promedio_driver`, `escuelas_con_dato`, `pct_escuelas_sin_dato`, `escuelas`)
  cayeron con la re-escala US-205; ahora usan `pct_escuelas_por_driver`, `escuelas_por_driver`,
  `pct_escuelas_sin_recomendacion`, `escuelas_con_recomendacion` y `cobertura_recomendacion`. Sin
  esto, `test_todo_chart_de_db05_apunta_a_dataset_y_metrica_declarados` (de #114) fallaba.
- **Guarda extendida a los 15 datasets virtuales** (13 US-205 + 2 db07/US-222) y allowlist +=
  `gold.cubo_completitud`: `test_son_exactamente_los_15_datasets_virtuales`, idem allowlist/métricas.
- Conteos finales del semántico: db01-02=47, db03-04=27, db05-08=53 (incluye tests de #114),
  db06-09=48, repunteo_cubos=34.

## Bloqueantes
- **Gate Deni** pendiente (re-materialización `gold.dim_driver` vs catálogo corto, BUG-015/BUG-022)
  — bloquea sincronizar DB-05/08 con datos reales en Superset.
- **ADR-007**: mesa convocada el 2026-08-29 (ver `_tmp-adr007-mesa-2026-08-29.md`, notas temporales);
  la decisión valida/revalida el umbral 0.6 que el repunteo ya asume. Cubos C1 siguen pendientes de
  ratificación formal antes de re-materializar.
- **BUG-027**: re-mapeo de `metrics_kpis_base_us221.yaml` (dueño Oscar Quiroz).
- **US-221 followup**: el stash "US-221 followup WIP + RETOMAR (ref Manuel)" guarda el WIP para
  retomar en su rama (después de este merge).

## Próximos pasos
- Revalidación contra datos con `sync_semantic_layer.py --validar-datos` tras gate Deni + ADR-007.
- DB-07 (US-222): Oscar debe registrar los 2 datasets y declarar el tablero (bloqueado hasta que el
  mock `gold_ml_outputs_mock.sql`/cubos estén cargados).
- BUG-029: darle ID al bloqueo que Oscar reportó (db09 leía `gold.recomendaciones`; el repunteo
  US-205 ya lo resolvió leyendo `gold.cubo_recomendaciones`).