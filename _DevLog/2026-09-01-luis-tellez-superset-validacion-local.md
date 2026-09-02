---
project: "FARO"
date: "2026-09-01"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — item 5 PROMPT-B: validar Superset en local + procedimiento de promoción"
touches: ["US-502", "US-203", "US-205", "REQ-002", "REQ-005", "BUG-029"]
tags: [devlog, superset, bi, validacion, deploy, carril-b]
---

# DevLog — 2026-09-01 — Superset validado en local (item 5) + procedimiento de promoción

→ [[_DevLog/_index|Volver al índice]] · [[superset/README|Convención de la capa semántica]]

## Contexto

Item 5 de la lista de remediación (PROMPT-B §6.5): levantar Superset, importar los tableros y **validar
estructura** de DB-01 y DB-02 en local — que rendericen, que el filtro de ciclo funcione, que no haya
charts rotos. **Los números NO se validan aquí** (dependen del recálculo del Carril A; solo hay un ciclo
cargado en el ambiente). El deploy **queda pendiente y no lo hago yo**; el entregable de código es dejar
escrito qué haría falta para promoverlo. Trabajé sobre el stack concurrente `project-analysis-status`
(DB en `127.0.0.1:5432`, Superset en `127.0.0.1:8088`), con autorización explícita para usarlo.

## Qué se validó (estructura, no números)

- **Sync completo sin errores:** `python superset/sync_semantic_layer.py --validar-datos` → exit 0, cero
  errores. Importó datasets + métricas + charts + los dos tableros.
- **DB-01 · Ejecutivo (US-203):** 9 charts, todos **✓ datos OK**; `published = true`.
- **DB-02 · Mapa de riesgo territorial:** 7 charts, incl. el **coroplético municipal (KPI-10)**
  `deck_polygon` con GeoJSON real; todos **✓ datos OK**; `published = true`.
- **Filtros nativos** cableados: `Ciclo escolar` (id_ciclo), `Entidad` (nombre_entidad), `Nivel
  educativo` (nivel). El **filtro de ciclo funciona**: ciclo real `2024-2025` → 5837 filas; ciclo
  inexistente → 0 (None). Ningún chart roto.
- URLs: `http://127.0.0.1:8088/superset/dashboard/db01-ejecutivo/` y `.../db02-mapa-riesgo/`.

## Qué hubo que arreglar en el AMBIENTE para poder validar

Nada de esto es código de este PR; son datos de runtime del stack compartido. Se documenta porque
**revela causas raíz del Carril A / orden de build** (ver §hallazgos):

1. **`gold.geo_municipio` era un *stub* de 10 filas** (nombres falsos, sin `geometria`, sin PK) porque
   ese stack corrió dbt **antes** de cargar geometrías (orden P-03 invertido). Sin `geometria`, el
   coroplético de DB-02 (INNER JOIN) tira 500 y **aborta el sync completo**. Poblé las 317 geometrías
   del asset versionado (mi territorio, paso 4 del README) con `ALTER ... ADD COLUMN IF NOT EXISTS` +
   *staging* temporal + `UPDATE...FROM` + `INSERT...WHERE NOT EXISTS`. **Aditivo, sin DELETE/DROP.**
2. **`gold.cubo_pivot` no estaba materializado** por el Carril A (DB-08). La materialicé desde el SQL
   compilado de dbt, reemplazando `p.probabilidad` por `null::double precision` (esa columna aún no
   existe en el esquema local de `gold.predicciones`). Placeholder: `dbt run` la reemplaza.
3. **Password admin de la metadata de Superset había derivado** del `.env` → `superset fab
   reset-password` (sin tocar código). *No* escribí la contraseña en ningún formulario de login del
   navegador (acción prohibida); validé por la API REST.

## Qué se dejó escrito (entregable de código)

`superset/README.md` → nueva sección **"Promoción a producción (pendiente · C5)"** con lo que pide el
item 5: **metadata DB** (aclara que **ya es PostgreSQL**, no SQLite — la compose fija
`DATABASE_DIALECT=postgresql`; en prod apuntar los `DATABASE_*` a una base `superset` en **Cloud SQL**
desde Secret Manager), **SECRET_KEY** (de Secret Manager, y cuidado al rotar: cifra las contraseñas de
las conexiones → `superset re-encrypt-secrets`), **rol invitado de solo lectura** (`faro_invitado`/
`Public`, sin SQL Lab ni upload, solo DB-01…DB-10, lo público lo decide el PO), prerequisitos
(orden P-03, cubos `gold.cubo_*` materializados, gunicorn en vez de `superset run`, Redis para caché) y
un checklist de promoción. **El deploy no se ejecuta en este PR** (CLAUDE.md §2.7).

## Hallazgos fuera de la lista (para §11 / owners)

- **Carril A (C1):** `cubo_pivot` y `cubo_escuela_360` no estaban materializados en el ambiente; falta
  `dbt run` de Gold. El esquema local de `gold.predicciones` **no tiene la columna `probabilidad`** que
  el SQL compilado ya referencia (el compilado va por delante del esquema materializado).
- **Orden de build P-03:** el *stub* de `geo_municipio` confirma que si dbt corre antes de la carga de
  geometrías, DB-02 truena. El README ya documenta la secuencia; conviene fijarla en el runbook del deploy.
- **Acoplamiento del sync (BUG-029):** `ensure_datasets` importa **todos** los `semantic/*.sql` en
  bloque; un solo 500 (cubo faltante, JOIN sin datos) aborta el import completo, incluidos DB-01/DB-02
  que sí estaban sanos. Ya está levantado como BUG-029; lo confirmo desde otro ángulo.
- **`kpi_01_matricula_total.sql`** es un huérfano **pre-repunteo**: lee `gold.fact_escuela_ciclo` (no el
  cubo, contra US-205) y usa el bind `:nivel`, inválido para los datasets de Superset. Ningún tablero lo
  referencia. Es archivo de **Manuel (US-201)** — **no lo toqué**; necesita su ratificación para
  corregirlo o retirarlo.

## Qué necesito del Carril A para la consolidación

- `dbt run` de Gold **después** de la carga de geometrías (P-03), materializando todos los `gold.cubo_*`
  (incl. `cubo_pivot`/`cubo_escuela_360`) con la columna `probabilidad` real.
- El recálculo/repunteo para que **los números** de DB-01/DB-02 sean correctos (hoy solo hay un ciclo).
- Decisión de Manuel sobre el huérfano `kpi_01_matricula_total.sql`.

## Seguridad / alcance

- Local-first: **no** se promovió nada a producción. Cambios al ambiente compartido: aditivos y sin
  DDL destructivo. No toqué territorio del Carril A en el repo (`dbt/**`, `src/**`); solo `superset/`.
- Sin credenciales ni contenido de `.env` en el código.
