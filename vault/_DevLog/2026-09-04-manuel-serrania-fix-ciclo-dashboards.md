---
project: "FARO"
date: "2026-09-04"
author_human: "Manuel Alejandro Serranía Reinada"
agent: "OpenCode"
model: "opencode/big-pickle"
session_duration: "2h"
touches: ["US-203", "US-204", "US-205", "US-213", "US-222", "REQ-002", "BUG-044", "BUG-047"]
tags: [devlog]
---

# DevLog — 2026-09-04 — Fix ciclo por defecto en 7 dashboards + filtro cct + migración st.html (BUG-047)

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué se hizo

**Cierre iterativo del PR abierto** atendiendo los comentarios del equipo. Work State de la sesión:
7 dashboards con bug de ciclo (espejo de BUG-044), migración `st.html()`, fix de caché + transporte,
`cct` para destrabar a Marina, y Streamlit en requirements.

- **BUG-047 dado de alta** (espejo de BUG-044 en dashboards). BUG-044 (C4, Karla) fija el ciclo en la
  API; los tableros no pasan por la API, leen la base directo, así que no estaban cubiertos. `high`,
  `fixed`, owner C2. ID según DEC-013: BUG-045 era el máximo en `main` al abrir esta rama. **Nota del PM (2026-09-04):** colisión con `dev/luis-tellez`, que registró BUG-046 en paralelo para un bug distinto (OAuth `at_hash`) partiendo del mismo commit — su PR mergea primero (critico/producción), este se renumera a BUG-047 antes del merge, sin cambiar nada del fix.
- **`valor_por_defecto: "2024-2025"` en 7 dashboards** que declaran `id_ciclo` y no fijaban ciclo al
  abrir: DB-01 ejecutivo, DB-02 mapa de riesgo, DB-05 analisis driver, DB-06 predicciones,
  DB-07 calidad cobertura, DB-08 explorador cubo, DB-09 recomendaciones. DB-03/DB-04 ya los cubrió
  Marina dentro de US-214a; DB-10 monitoreo no declara `id_ciclo` y no aplica.
- Mecanismo **aditivo y opt-in** en `sync_semantic_layer.py:1090`: la clave opcional se traduce al
  `defaultDataMask` de Superset; sin la clave el tablero no cambia (compatibilidad hacia atrás
  exigida por prueba). Los tableros de Manuel/Monserrat/Oscar no cambian.
- **`1_Dashboards.py`**: `st.components.v1.html` → `st.html()` (deprecado a remover tras 2026-06-01;
  `st.iframe` no conserva borde/border-radius + `allow=fullscreen`); `st.html()` no acepta
  `height`/`scrolling` — se quitaron (el iframe inline define `height="800"`). Selectbox de ciclo fija
  `index=len(CICLOS)-1` (2024-2025). Fix de caché + transporte: `st.cache_data.clear()` +
  `_tableros.clear()` en `except SupersetDeshabilitado`/`except SupersetError` y nuevo
  `except httpx.HTTPError`.
- **Causa raíz del test en secuencia** (Christian diagnosticó mal): no es `st.cache_data` —
  AppTest comparte `sys.modules` entre `.run()` y `superset_client.SUPERSET_URL` queda congelada del
  test previo → "Connection refused". El fixture purga `sys.modules` de
  `MODULOS_FRONTEND = ("superset_client", "auth", "1_Dashboards")` + `streamlit.cache_data.clear()`
  pre/post.
- **`cct` al final de `filtros_globales`** (índice 3) en DB-06 y DB-09: los IDs se generan por
  posición, insertar en medio rompe el drill-down de Marina (DB-03→DB-06/DB-09) sin error visible.
- **`requirements.txt` raíz: `streamlit==1.62.0`** — el CI solo instala el `requirements.txt` raíz, así
  que los tests de frontend se saltaban en silencio (hallazgo Marina/Christian, pre-merge). Precedente:
  "solo lo que el CI necesita para correr las pruebas" (scikit-learn).

## Verificación

- Suite de la célula (frontend + capa semántica + sync + filtro ciclo): **226 passed**, incluido
  `tests/test_frontend_dashboards_streamlit.py` (33, los 3 antes-saltados ahora corren).
- `ruff check` limpio · ownership `test_check_ownership.py` 40 passed · `vault_lint` limpio.
- En la suite observable completa del ambiente se ven 21 `failed` en tests de validación
  (`great_expectations`, `'project_root_dir' and 'context_root_dir' are conflicting args` — conflicto
  de versión preexistente, ajeno) y 12 módulos que no colectan por faltar `limits` (slowapi de
  `src/api`) — ambos preexistentes, documentados igual que en el DevLog del 2026-09-02.

## 🤖 Sesión de IA

- **Agente / modelo:** OpenCode / opencode/big-pickle
- **Archivos creados/modificados:**
  - `superset/dashboards/db01_ejecutivo.yaml`, `db02_mapa_riesgo.yaml`, `db05_analisis_driver.yaml`,
    `db06_predicciones.yaml`, `db07_calidad_cobertura.yaml`, `db08_explorador_cubo.yaml`,
    `db09_recomendaciones.yaml` — `valor_por_defecto` (+ `cct` en db06/db09)
  - `superset/sync_semantic_layer.py` — mecanismo `valor_por_defecto`/`defaultDataMask`
  - `src/frontend/pages/1_Dashboards.py` — `st.html()`, `index=len(CICLOS)-1`, cache clear,
    `except httpx.HTTPError`
  - `tests/test_frontend_dashboards_streamlit.py` — fixture purga `sys.modules`
  - `requirements.txt` — `streamlit==1.62.0`
  - `vault/06_Quality_Testing/Bug_Register.md` — BUG-047 dado de alta + sección de detalle
  - `vault/02_Requirements/Traceability_Matrix.md` — fila de evidencia incremental
  - `vault/_DevLog/_index.md` — entrada de esta sesión
- **IDs tocados:** US-203, US-204, US-205, US-213, US-222, REQ-002, BUG-044 (espejo), BUG-047 (nuevo)

## Próximo paso

Commit del PR e iteración. Respuesta redactada por persona: Oscar (DB-07 cubierto, DB-10 no aplica,
revisor de DB-07 en PR), Luis (BUG-044 espejo en dashboards cubierto aquí), Marina (cct en DB-06/DB-09),
Christian (causa raíz real del test en secuencia + streamlit en requirements), Deni (geojson + script
listos, requiere Postgres corriendo).
