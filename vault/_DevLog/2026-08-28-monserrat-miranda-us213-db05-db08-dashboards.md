---
project: "FARO"
date: "2026-08-28"
author_human: "Monserrat Xcaret Miranda Olivas"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión larga: cierre administrativo de US-211b + US-213 completo (DB-05 tabs D1-D6, DB-08 pivote), soporte de tabs/markdown en sync_semantic_layer.py, validación contra Gold real"
touches: ["US-213", "US-211b", "REQ-002", "BUG-015", "BUG-016"]
tags: [devlog, bi, dashboards, superset, celula-2]
---

# DevLog — 2026-08-28 — US-213: DB-05 (tabs D1-D6) y DB-08 (explorador) + validación real

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

Sesión de retoma del repo tras el cierre de US-211b (PR #73, ya `done` desde el 25-ago según
`Execution_Status.md`, aunque mi tabla personal §9 seguía sin reflejarlo). Objetivo: cerrar ese
detalle administrativo y arrancar/cerrar US-213 (Sprint 4) — construir DB-05 y DB-08 sobre el
contrato semántico de US-211b.

## Qué se hizo

### 1. Cierre administrativo de US-211b
- Confirmado `done` oficial desde 2026-08-25 (`Execution_Status.md`, evidencia PR #73/#78, DEC-009).
- Actualizada mi tabla personal (§9 de este plan) de "🔵 En revisión / 95%" a "✅ Terminado / 100%".

### 2. BUG-015 — hallazgo de Manuel/Diana sobre `gold.dim_driver`
Manuel encontró (DevLog 27-ago) que `gold.dim_driver` local queda con esquema viejo (nombres largos
de mock) en vez del seed canónico (`fuente`/`cobertura`/`nivel_geografico`), bloqueando el sync de
DB-05/08 con `HTTP 500`. Diana lo confirmó y validó el fix (`dbt seed --select dim_driver
--full-refresh`) al día siguiente, pero nadie lo había registrado formalmente. Dado de alta como
**BUG-015** en `Bug_Register.md`. Pendiente: comunicárselo directamente a Diana (fuera del repo).

### 3. Coordinación con Manuel — Path A (tabs) + soporte MARKDOWN
US-213 pide "un tab por driver D1-D6", pero `superset/dashboards/*.yaml` solo soportaba layout plano
(`ROOT_ID→GRID_ID→ROW→CHART`), usado por los 6 tableros ya sincronizados. Le planteé dos caminos a
Manuel (dueño de la convención US-202): extender `sync_semantic_layer.py` con tabs reales (Path A) o
simular tabs con secciones tituladas sin tocar el script (Path B). Aprobó **Path A**, con
condiciones: cambio aditivo y aislado (la ruta plana no se toca), filtro por driver vía
`params_extra.adhoc_filters` (no hay `adhoc_filters` de primera clase en el script), validar con 1
chart manual antes de escribir los 6 juegos, y él revisa el PR directo por tocar el script
compartido de 8 tableros. Un segundo mensaje agregó soporte de nodos `MARKDOWN` (nota de fuente por
driver, texto estático, mismo PR) — también aprobado, con la misma regla de validar 1 nodo manual
antes de aplicarlo a los 6 tabs.

### 4. `superset/sync_semantic_layer.py` — `_layout_tabs()` (aditivo)
Función hermana de `_layout_grilla()`: árbol `ROOT_ID(TABS) → TAB-<id> → GRID-<id> → filas →
CHART|MARKDOWN`. `ensure_dashboard()` gana una rama `usa_tabs` (activa solo si el YAML trae `tabs:`
en la raíz) — el camino de los 4 tableros existentes queda exactamente igual. Nodo `MARKDOWN` con
`meta.code` estático, id determinístico `MD-{tab}-0`, primera fila del grid del tab.

### 5. `superset/dashboards/db05_analisis_driver.yaml` (nuevo) — DB-05, 6 tabs
Un tab por driver (D1-D6), mismo juego de 6 charts por tab (4 tiles KPI + evolución por ciclo + tabla
municipal), filtrado por su propio `id_driver` vía `adhoc_filters`, con nota de fuente (Cube_Specs
§3.3) como nodo `MARKDOWN`. Nombres de chart prefijados por driver (blindaje BUG-011: mismo dataset
en los 6 tabs). Filtro global "Entidad" usa `nombre_entidad` (legible), no `cve_ent` (lo que dice
literalmente el contrato) — coherencia de UX con los 4 tableros ya construidos, decisión registrada
en el propio YAML.

### 6. `superset/dashboards/db08_explorador_cubo.yaml` (nuevo) — DB-08, explorador libre
3 tiles de contexto (matemáticamente seguros sin agrupar por driver) + tabla dinámica libre
(`pivot_table_v2`, `groupbyColumns: [id_driver, nombre_driver]`) + tabla de detalle sin agregar.
`matricula_total` deliberadamente **no** preseleccionada en el pivote (se repite x6 por escuela,
riesgo de doble conteo si se suma sin agrupar por `id_driver` — Cube_Specs §2.2/§4.3).

**Pendientes de UX documentados en el header del YAML (candidatos a US-215b, revisados en vivo
contra Superset real):**
- `nombre_municipio`/`nombre_escuela` muestran placeholders literales ("Municipio 09002", "Escuela
  09DJN0001A") — vienen así de los fixtures compartidos del equipo
  (`bronze_coneval_sample.csv`/`bronze_cct_sample.csv`), no de este SQL/YAML. Pendiente de que el
  equipo decida si se deja anonimizado o se mejora el fixture.
- `cct` no es autoexplicativo fuera del dominio — candidato a verbose_name/tooltip.
- La columna D5 (agua) desaparece de la sección `valor_driver` del pivote cuando es 100% `SIN_DATO`
  (Superset omite la columna en vez de mostrar 0 — correcto según R2, pero puede leerse como que el
  driver no existe). La tabla de detalle sí lo muestra bien (`N/A` + `SIN_DATO`).

### 7. Validación contra Gold real (no solo mock)
Levanté el pipeline local completo: `dbt-core`/`dbt-postgres` instalados en el venv,
`~/.dbt/profiles.yml` fuera del repo (contraseña vía `env_var`, nunca hardcodeada), 9 fixtures de
bronze cargados (`src/ingesta/cargar_bronze_fixture.py`), `dbt seed` + `dbt run --full-refresh`.
`gold.cubo_driver`/`gold.cubo_pivot` materializados con datos reales (150 filas c/u sobre 25
escuelas). `python superset/sync_semantic_layer.py --validar-datos` corrió contra Gold real: los 36
charts de DB-05 y los 5 de DB-08 responden `✓ datos OK`, sin romper los 9 tableros ya construidos por
el equipo (61 charts previos, todos siguen en verde).

### 8. BUG-016 — condición de carrera en `dbt run` con threads>1
Al correr `dbt run --full-refresh` con el default de 4 threads, `gold.dim_escuela`,
`gold.dim_municipio` y `gold.dim_tiempo` truenan con `relation "silver.<tabla>" does not exist`,
aunque esa silver se crea casi al mismo instante — con `--threads 1` corre limpio. Hallazgo nuevo
(no documentado antes por nadie del equipo), dado de alta como **BUG-016** (severidad `high`,
hipótesis: esos 3 modelos no usan `{{ ref() }}` hacia su fuente silver).

## Cómo se probó

```bash
pytest tests/test_semantic_db05_db08.py -v   # 51/51 passed
pytest tests/ -q                              # 488 passed, 5 skipped (sin relación: streamlit no
                                               # instalado, fixture de ML sin generar)
python superset/sync_semantic_layer.py --validar-datos   # contra Gold real (dbt), 9 tableros en verde
```

## Archivos tocados

- `superset/sync_semantic_layer.py` — `_layout_tabs()` + rama `usa_tabs` en `ensure_dashboard()`
- `superset/dashboards/db05_analisis_driver.yaml` (nuevo)
- `superset/dashboards/db08_explorador_cubo.yaml` (nuevo)
- `tests/test_semantic_db05_db08.py` — +21 pruebas (layout de tabs, dashboards DB-05/DB-08, guarda
  de doble conteo del pivote)
- `vault/06_Quality_Testing/Bug_Register.md` — BUG-015, BUG-016
- `vault/12_Roadmap_Sprints/Sprints/2-monserrat-xcaret-miranda-olivas.md` — §9 actualizado (US-211b 100%,
  US-213 en curso)
- `vault/02_Requirements/Traceability_Matrix.md` — fila REQ-002, evidencia de US-213
- `vault/_DevLog/_index.md`

## 🤖 Sesión de IA

- **Agente/modelo:** Claude Code / claude-sonnet-5
- **Decisiones autónomas de fondo:** ninguna sin aprobación explícita — el cambio a
  `sync_semantic_layer.py` (tabs + markdown) se coordinó con Manuel Serranía antes de escribirse; el
  filtro `nombre_entidad` vs `cve_ent` y las 6 métricas del pivote se presentaron para revisión antes
  de guardarse. Todo archivo nuevo o modificado se mostró para aprobación línea por línea antes de
  escribirse en disco.
- **Manejo de secretos:** `~/.dbt/profiles.yml` vive fuera del repo, contraseña vía `env_var`, nunca
  hardcodeada; verificado que `.env`/`.dbt` no aparecen en `git status` en ningún momento de la
  sesión.

## Seguridad/calidad

- [x] `pytest tests/test_semantic_db05_db08.py -v` → 51 passed
- [x] `pytest tests/ -q` → 488 passed, 5 skipped (sin relación al alcance de esta sesión)
- [x] `python vault/_Meta/scripts/vault_lint.py .` → ✅ Vault limpio
- [x] Sin secretos hardcodeados; credenciales verificadas fuera de git status
- [x] Validado contra Gold real (dbt), no solo mock

## Bloqueantes

- Ninguno de fondo. Acordado con Manuel Serranía que **Edgar Coronel (PM) revisa/aprueba el PR**;
  Manuel también lo revisa (dueño de la convención US-202, ya dio su visto bueno de diseño en chat
  para tabs + markdown) pero no es bloqueante.
- BUG-015 y BUG-016 son de Célula 1 (Diana) — no bloquean el cierre de este PR, pero si BUG-015 no se
  resuelve de forma compartida, cada dev necesita correr `dbt seed --select dim_driver
  --full-refresh` localmente antes de sincronizar DB-05/08 contra Gold real.

## Próximos pasos

1. Commit + abrir el PR (`feat/monserrat-olivas-us213-db05-db08-dashboards`), Edgar como reviewer
   principal, Manuel como revisor no bloqueante.
2. Enviar al chat grupal el mensaje pendiente sobre BUG-015/BUG-016 (dirigido a Diana).
3. US-214b (filtros/drill-down) y US-215b (usabilidad — incluye los 3 pendientes de UX documentados
   arriba) quedan para Sprint 5.
