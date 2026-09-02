---
project: "FARO"
date: "2026-08-30"
author_human: "Monserrat Xcaret Miranda Olivas"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión larga: avance de US-214b (drill-down DB-05→DB-08) y US-215b (plan de pruebas de usabilidad/accesibilidad), validado en vivo contra Superset 6.1.0 real en Docker local"
touches: ["US-214b", "US-215b", "REQ-002", "BUG-027", "BUG-037"]
tags: [devlog, bi, dashboards, superset, celula-2]
---

# DevLog — 2026-08-30 — US-214b (drill-down DB-05→DB-08) y US-215b (plan de pruebas)

→ [[_DevLog/_index|Volver al índice]]

## Contexto

Continuación de la misma sesión que cerró US-211b/US-213 (PR aparte, #161). Con el repo actualizado
y el PR #134 de Manuel (US-205, repunteo de DB-05) revisado y confirmado limpio, se arrancó un
segundo PR para adelantar **US-214b** (filtros/drill-down entre DB-05 y DB-08) y **US-215b** (plan de
pruebas de usabilidad/accesibilidad), en rama `feat/monserrat-olivas-us214b-us215b-avance`.

## Qué se hizo

### 1. Investigación previa (US-214b)

Cross-filtering y "Drill to Detail" nativos de Superset son ambos **solo dentro del mismo
dashboard** — no sirven para saltar de DB-05 a DB-08. El mecanismo real es una columna calculada con
un link HTML (`<a href="...">`) hacia una URL de DB-08 con el parámetro `native_filters`
(RISON-encoded) preseleccionando `(cve_mun, id_driver)`, más `allow_render_html: true` en el chart —
mismo mecanismo de *passthrough* de `params_extra` que ya usan `adhoc_filters` y el pivote de DB-08.
Superset no tiene una feature nativa de "columna tipo link" (SIP-77 fue propuesta y rechazada).

### 2. Validación en vivo antes de comprometerse al diseño

Se levantó Docker local (`db` + `superset`, imagen reconstruida) y se confirmó **Superset 6.1.0**
corriendo (misma versión que el equipo confirmó el 21-ago). Antes de construir nada, se verificó
contra el código y los bundles reales del contenedor:
- `allow_render_html` existe tal cual en el control de Table/Pivot Table ("Render columns in HTML
  format") — confirmado en el bundle JS compilado de esta versión exacta.
- El sanitizador es **DOMPurify** (confirmado en el bundle), cuyo default permite `<a href="...">`
  con URLs http(s)/relativas.
- El formato exacto de RISON para `native_filters` se obtuvo de la propia fuente de Superset
  (`superset/reports/models.py::_generate_native_filter`, el mecanismo real de reportes con filtros
  pre-seleccionados) y se generó con su propia librería `prison` para tener el string exacto, en vez
  de adivinarlo: valores con forma numérica (`cve_mun`) se citan (`!('09001')`, con el workaround
  documentado del backend de reemplazar `'` por `%27`); valores alfanuméricos (`id_driver`, D1-D6) no.

### 3. Bloqueo real encontrado y desviado sin tocar archivos ajenos

Al primer intento de sync completo, `sync_semantic_layer.py` abortó por completo antes de llegar a
dashboards: `superset/semantic/kpi_01_matricula_total.sql` (de Manuel, marcado "NO MODIFICAR sin
ratificación") usa `WHERE e.nivel = :nivel`, un bind-param sin valor al momento de crear el dataset —
Postgres lo rechaza. Es la misma causa raíz que **BUG-027** (ya registrado por Marina, ratificado por
Manuel para borrarse junto con sus 4 archivos hermanos, seguimiento pendiente de Oscar Quiroz/C2), no
un bug nuevo — se agregó una nota fechada a BUG-027 con la evidencia de hoy (el pendiente de borrado
ya no es solo una referencia rota que nadie lee: tumba cualquier sync completo) y se subió su
severidad de `low` a `medium`. Mitigación de hoy: el archivo se apartó **solo en disco local**, nunca
en git, a la carpeta temporal de la sesión, y se devolvió a su lugar antes de este commit.

### 4. Implementación de US-214b (validado con 1 tab antes de replicar a los otros 5)

- `superset/dashboards/db08_explorador_cubo.yaml`: 2 filtros globales nuevos (`cve_mun`, `id_driver`).
- `superset/semantic/db05_cubo_driver.sql`: columna calculada `link_db08` (link HTML con
  `native_filters` RISON hacia DB-08). Texto del link decidido solo para DB-05 ("Ver detalle del
  municipio →"); homologación de nomenclatura con otros tableros queda pendiente, no bloqueante.
- `superset/dashboards/db05_analisis_driver.yaml`: `link_db08` en `dimensiones` + `allow_render_html:
  true` en las 6 tabs (D1 primero, validado en navegador real por la reportante, luego D2-D6).
- **Validación real en navegador (no solo API)**: clic en el link de dos filas distintas (municipios
  09003 y 19039) confirmó que DB-08 llega con el filtro de Municipio y Driver correctos — el chart
  "Valor promedio del driver" cambió de 0.10 a 0.90 entre una y otra, evidencia de que el filtro sí
  se aplicó (no solo que la URL cargó).
- `04_UX_Design/Cube_Specs_DB05_DB08.md` §3.4: ruta DB-05→DB-08 pasa de "⬜ Propuesta" a "✅
  Ratificada". `metrics_db05_db08.yaml`: bloque `drill_down:` gana la entrada DB-05→DB-08.

### 5. BUG-037 — hallazgo nuevo durante la validación

Al agregar `link_db08` y volver a sincronizar, el chart de la tabla municipal reventó con `Columns
missing in dataset` — para `link_db08` **y** para 3 columnas preexistentes. Causa: `PUT
/api/v1/dataset/<id>` actualiza el texto del SQL pero Superset nunca vuelve a leer las columnas; solo
lo hace al crear el dataset. Mitigado a mano con `PUT /api/v1/dataset/<id>/refresh` (endpoint que
Superset ya expone). Registrado como **BUG-037**; el fix de fondo (llamar ese endpoint automáticamente
tras cada actualización de SQL en `ensure_datasets()`) queda propuesto, no aplicado hoy — es
`sync_semantic_layer.py`, herramienta compartida.

### 6. US-215b — plan de pruebas de usabilidad/accesibilidad

`06_Quality_Testing/Usability_Accessibility_Test_Plan_DB05_DB08.md` (nuevo, `DOC-USABILIDAD-DB0508`),
calcando el formato de `Physical_Test_Plan.md`. Adapta (no copia íntegro) el checklist de
`04_UX_Design/Accessibility.md`, acotado a lo verificable en un dashboard de Superset embebido —
excluye explícitamente ARIA de componentes propios de FARO Web y `prefers-reduced-motion` (US-206/
US-207, Manuel). 3 casos ya verificados hoy en vivo (el link y su filtro en DB-08); el resto queda
`⏳ pendiente` para una siguiente pasada. Documenta 2 huecos reales del proyecto sin rellenarlos por
cuenta propia: no hay CI de accesibilidad real, y no hay paleta de colores documentada para
"colorblind-safe".

## Cómo se probó

```bash
docker compose up -d db superset                       # Superset 6.1.0 confirmado
python superset/sync_semantic_layer.py                 # 9 dashboards, 19 datasets, sin errores
# validación manual en navegador: clic en link_db08 desde 2 filas distintas de DB-05,
# confirmado el filtro correcto en DB-08 (ver §4 arriba)
```

## Archivos tocados

- `superset/dashboards/db08_explorador_cubo.yaml` — +2 `filtros_globales`
- `superset/semantic/db05_cubo_driver.sql` — +columna `link_db08`
- `superset/dashboards/db05_analisis_driver.yaml` — `link_db08` + `allow_render_html` en 6 tabs
- `04_UX_Design/Cube_Specs_DB05_DB08.md` — §3.4 ratificada
- `superset/semantic/metrics_db05_db08.yaml` — `drill_down:` +DB-05→DB-08
- `06_Quality_Testing/Usability_Accessibility_Test_Plan_DB05_DB08.md` (nuevo)
- `06_Quality_Testing/_index.md`
- `06_Quality_Testing/Bug_Register.md` — nota fechada en BUG-027 (severidad low→medium), BUG-037 nuevo
- `12_Roadmap_Sprints/Sprints/2-monserrat-xcaret-miranda-olivas.md` — §9 actualizado
- `02_Requirements/Traceability_Matrix.md` — fila REQ-002, evidencia de US-214b/US-215b
- `_DevLog/_index.md`

## 🤖 Sesión de IA

- **Agente/modelo:** Claude Code / claude-sonnet-5
- **Decisiones autónomas de fondo:** ninguna sin aprobación explícita. Cada archivo se mostró como
  diff antes de escribirse; el hallazgo de `kpi_01_matricula_total.sql` (de Manuel) se resolvió
  apartando el archivo solo en disco local, nunca en git, con autorización explícita previa; el
  hallazgo de BUG-037 (fix de fondo en `sync_semantic_layer.py`, herramienta compartida) se dejó
  solo documentado, sin tocar el script, por decisión explícita de la reportante.
- **Manejo de secretos:** credenciales de `.env` usadas solo para autenticar contra el Superset local
  de Docker; no se hardcodearon en ningún archivo del repo.

## Seguridad/calidad

- [x] `pytest tests/test_semantic_db05_db08.py -v` → 53 passed
- [x] `pytest tests/ -q` → 643 passed, 5 skipped (sin relación al alcance de esta sesión)
- [x] `python _Meta/scripts/vault_lint.py .` → ✅ Vault limpio
- [x] Sin secretos hardcodeados
- [x] Validado en vivo contra Superset 6.1.0 real (no solo por API/estático)
- [x] `kpi_01_matricula_total.sql` restaurado a su lugar antes de este commit (verificado con `git
      diff` — sin cambios contra lo ya versionado)

## Bloqueantes

- Ninguno de fondo. BUG-027 (pendiente de Oscar Quiroz/C2) y BUG-037 (pendiente de dueño de
  `sync_semantic_layer.py`) no bloquean este PR — se mitigaron localmente para poder validar.

## Próximos pasos

1. Commit (IDs `US-214b`/`US-215b`) + push + abrir PR 2.
2. Completar los casos `⏳ pendiente` del plan de pruebas de usabilidad/accesibilidad en una
   siguiente pasada.
