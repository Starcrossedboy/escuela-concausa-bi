---
project: "FARO"
date: "2026-08-22"
author_human: "Monserrat Xcaret Miranda Olivas"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión única: contrato semántico + SQL + YAML + pruebas de US-211b"
touches: ["US-211b", "REQ-002", "DOC-CUBESPEC-DB0508", "SPRINT-MONSERRAT-XCARET-MIRANDA"]
tags: [devlog, bi, cubos, capa-semantica, celula-2]
---

# DevLog — 2026-08-22 — Contrato semántico y capa semántica de DB-05/DB-08 (US-211b)

## Qué se hizo

Cierre de **US-211b** (Sprint 3, Célula 2 — Analytics & BI): modelado de métricas, jerarquías y
granos de los cubos que alimentan **DB-05 (Análisis por driver)** y **DB-08 (Explorador del
cubo)**, siguiendo la convención de capa semántica fijada por Manuel Serranía (`superset/README.md`,
US-202) y el patrón ya cerrado de Marina García del Buey para DB-03/DB-04 (US-211a).

- **`04_UX_Design/Cube_Specs_DB05_DB08.md`** (`DOC-CUBESPEC-DB0508`, nuevo) — contrato semántico
  completo: grano y columnas de `gold.cubo_driver` y `gold.cubo_pivot`, catálogo de los 6 drivers
  con su fuente/ADR/estado real (D5/agua sigue en `SIN_DATO` 100% — DS-06 pendiente), jerarquías y
  drill-down, mapeo a KPIs, contrato de dependencias y las dos solicitudes formales (§8).
- **`superset/semantic/db05_cubo_driver.sql`** (nuevo) — grano propuesto `id_driver × cve_mun ×
  nivel × ciclo`, formato largo (unpivot vía `UNION ALL` de `d1`…`d6`), componentes aditivos
  (`suma_valor`/`escuelas_con_dato`), sin `LEFT JOIN` a ML (v1 no lo necesita).
- **`superset/semantic/db08_cubo_pivot.sql`** (nuevo) — grano `cct × id_driver × ciclo`, mismo
  unpivot pero sin agregación (grano de detalle, como `db03_cubo_escuela_360.sql`).
- **`superset/semantic/metrics_db05_db08.yaml`** (nuevo) — métricas/jerarquías/filtros globales,
  `dimension_obligatoria_en_agregacion: id_driver` en ambos datasets, KPI-19/KPI-20 propuestos,
  `pct_escuelas_sin_dato` reusa KPI-06.
- **`tests/test_semantic_db05_db08.py`** (nuevo) — 22 funciones de prueba estática (29 casos con
  parametrización), **29/29 en verde**: SIN_DATO nunca cero, v1 sin salidas de ML, formato largo
  (unpivot de los 6 drivers), grano/GROUP BY, filtros globales, y las reglas del YAML (NULLIF en
  toda división, sin COALESCE, KPI-19/20 propuestos, KPI-06 reusado, cambio de grano documentado
  solo en `cubo_driver`).
- Se instaló Python 3.11.9 (winget, fuente oficial) y se creó `.venv/` — el ambiente local del §4
  del plan de sprint no estaba configurado todavía (0 commits/PRs previos). Se corrigieron 6
  wikilinks rotos a los ADR (`ADR-005-dim-driver-mapeo`, `ADR-006-idw-calidad-aire-agua` — el
  nombre real del archivo lleva sufijo) encontrados por `vault_lint.py`.
- **`_DevLog/_index.md`** — fila nueva registrando esta sesión.

## 🤖 Sesión de IA

**Agente/modelo:** Claude Code / claude-sonnet-5.

**Archivos tocados:** los 5 listados arriba (todos nuevos, dentro del alcance 🟢 de
`09_AI_Governance/Agent_Contexts/monserrat-miranda-agent-context.md`) + `_DevLog/_index.md`.
**No se tocó** `Data_Model.md`, `Screen_Specs.md`, `superset/sync_semantic_layer.py` ni nada bajo
`dbt/`.

**Decisión autónoma más relevante:** modelar ambos cubos en **formato largo** (una fila por
driver) en vez del formato ancho que usan DB-03/DB-04, para que DB-05 pueda mostrar "un tab por
driver" (US-213) sin duplicar 6 juegos de charts. Es una desviación del precedente directo, así
que se documentó explícitamente (Cube_Specs §2.2), se advirtió el riesgo de doble conteo que trae
consigo, y se fijó una mitigación verificable por test
(`dimension_obligatoria_en_agregacion: id_driver` + pruebas dedicadas) en vez de dejarlo solo como
nota de prosa. Se deja como solicitud abierta a Manuel (§8.3) que ratifique el patrón.

**Otra decisión documentada:** v1 de estos dos cubos no lee salidas de ML (`LEFT JOIN` a
`gold.predicciones`/`gold.recomendaciones`), a diferencia de DB-03/DB-04 — se registró como
decisión explícita (Cube_Specs §2.1), no como omisión, con test de regresión.

**Correcciones manuales:** pendiente — Monserrat revisa línea por línea antes de cualquier commit
(regla de su Agent Context).

## Seguridad/calidad

- [x] Sin credenciales, tokens ni contenido de `.env` en ningún archivo.
- [x] `pytest tests/test_semantic_db05_db08.py -q` → **29 passed**.
- [x] `pytest tests/ -q` (suite completa) → **297 passed, 4 skipped** — sin regresiones sobre lo
      existente.
- [x] `python _Meta/scripts/vault_lint.py .` → **✅ Vault limpio** (tras corregir 6 wikilinks
      rotos a los ADR).
- [x] DevLog enlaza los IDs tocados (`US-211b`, `REQ-002`, `DOC-CUBESPEC-DB0508`).

## Bloqueantes

- **§8.1 (Diana Álvarez)** — cambio de grano de `cubo_driver` a `driver × municipio × nivel ×
  ciclo`, pendiente de confirmación. **No bloquea**: el SQL de referencia ya trae el grano
  propuesto.
- **§8.3 (Manuel Serranía)** — alta de KPI-19/KPI-20 y ratificación del formato largo como
  convención válida. **No bloquea** el cierre de esta historia.
- US-213 (Sprint 4) seguirá esperando a que Célula 1 materialice `gold.cubo_driver`/`cubo_pivot`
  en US-113, igual que le pasa a US-212 con DB-03/DB-04.

## Próximos pasos

1. Actualizar `12_Roadmap_Sprints/Sprints/2-monserrat-xcaret-miranda-olivas.md` §9,
   `02_Requirements/Traceability_Matrix.md` (fila REQ-002) y `04_UX_Design/_index.md` — pendiente
   de confirmación explícita de Monserrat antes de tocar estos archivos compartidos.
2. Abrir rama `feat/monserrat-olivas-us211b-cubos-db05-db08`, commits por Conventional Commits,
   PR solicitando revisión de `@mserraniaa-png` (Manuel, técnica) y `@edgarcoroneln` (Edgar, PM —
   obligatoria por CODEOWNERS/DEC-003).
3. Cerrar al 100% cuando Diana y Manuel respondan §8.1/§8.3 — mismo patrón que el cierre de
   US-211a el 21-ago.
