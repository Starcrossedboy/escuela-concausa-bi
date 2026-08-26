---
project: "FARO"
date: "2026-08-23"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (Cowork)"
model: "claude-sonnet-5"
session_duration: "corta -- revisión de bloqueantes por Teams y registro de decisión"
touches: ["DEC-009", "DEC-008", "REQ-002", "US-113", "US-211b", "US-203"]
tags: [devlog]
---

# DevLog — 2026-08-23 — DEC-009: grano `nivel` en cubo_matricula/cubo_riesgo_territorial/cubo_driver/cubo_completitud

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo

Diana recibió por Teams tres mensajes con posibles bloqueantes y se revisaron en sesión:

- **Manuel (US-203):** avisó que quedaba pendiente "de su lado" (C1) el fix del Dockerfile de
  Superset (`uv pip` vs `pip`, causaba `No module named 'psycopg2'`). Verificado contra
  `docker/superset.Dockerfile` en `origin/main`: **ya está resuelto** — Manuel lo aplicó él mismo
  dentro de su propio PR #71 (ya mergeado) porque lo bloqueaba a él. No requiere ninguna acción de
  Diana; el aviso llegó desactualizado respecto al estado real del repo.
- **Deni (US-113)** y **Monserrat (US-211b)** señalaron, de forma independiente pero sobre el
  mismo problema, que 4 cubos de `Data_Model.md` §4.3 no tienen `nivel` en su grano y por lo tanto
  no pueden cumplir el filtro global de nivel educativo de AC-002.2:
  - `gold.cubo_matricula` (DB-01, DB-06): `entidad × municipio × ciclo` → sin `nivel`
  - `gold.cubo_riesgo_territorial` (DB-02): `municipio × ciclo` → sin `nivel`
  - `gold.cubo_driver` (DB-05): `driver × municipio × ciclo` → sin `nivel`
  - `gold.cubo_completitud` (DB-07): `municipio × driver × ciclo` → sin `nivel`

  Es el mismo problema que Diana ya resolvió una vez el 14-ago para `cubo_comparador_municipio`
  (**DEC-008**, a partir del hallazgo de Marina en US-211a): un cubo ya agregado no se puede
  desagregar después, así que el grano correcto hay que fijarlo antes de materializar.

## Verificación antes de confirmar

Antes de aprobar el cambio se validó que no rompiera ni complicara nada:

- **`superset/semantic/db01_cubo_matricula.sql` y `db02_cubo_riesgo_territorial.sql`** (Manuel,
  PR #71, ya mergeado): los datasets virtuales de Superset **ya están construidos asumiendo el
  grano nuevo** (`cve_mun × nivel × id_ciclo`) y el patrón de componentes aditivos de DEC-008,
  con el comentario explícito de que al existir el cubo real el swap será
  `SELECT * FROM gold.cubo_X` sin tocar nada más. Mantener el grano viejo (sin `nivel`) habría
  **roto** ese plan ya entregado, no confirmarlo.
- **`04_UX_Design/Cube_Specs_DB05_DB08.md` §8.1** (Monserrat, rama
  `feat/monserrat-olivas-us211b-cubos-db05-db08`, sin PR abierto aún, no bloqueante): ya entregó
  el SQL de referencia de `cubo_driver` (`superset/semantic/db05_cubo_driver.sql`) con el grano
  `driver × municipio × nivel × ciclo`. También documentó que `cubo_pivot` (DB-08) **no** necesita
  cambio — su grano a nivel CCT ya trae `nivel` gratis vía `dim_escuela`, igual que
  `cubo_escuela_360` (DB-03).
- `cubo_completitud`: nadie ha construido nada todavía sobre él (ni SQL de referencia ni
  dashboard), así que es el cambio de menor riesgo de los cuatro — evita que se construya mal y
  haya que rehacerlo.
- No afecta el trabajo propio de Diana en sesión (PR #74, fix D6 IDW de `fact_escuela_ciclo`/
  `features_escuela` — grano CCT, tablas distintas) ni RISK-007 (`gold.matricula_municipio_nivel`,
  que ya usa `nivel` en su grano desde el 22-ago). Se resuelve antes de US-106 (congelar esquema,
  vence 6-sep), que es el orden correcto.

## Decisión

Diana (Tech Lead Célula 1, regla 7 del vault) confirmó extender el patrón de DEC-008 a los 4
cubos. Registrada como **DEC-009** en `10_Risk_Governance/Decision_Log.md`, con el detalle
completo de granos anteriores/nuevos, y actualizado `03_Architecture/Data_Model.md` §4.3 (tabla
de granos + nota de diseño, mismo formato que la nota existente de DEC-008).

Respuesta enviada a Deni y Monserrat en Teams confirmando el criterio, citando la evidencia de
consistencia con el trabajo ya mergeado de Manuel, y dejando a Deni libre de materializar bajo
este grano para US-113.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude (Cowork), claude-sonnet-5
- **Archivos creados/modificados:**
  - `10_Risk_Governance/Decision_Log.md` (nueva fila DEC-009)
  - `03_Architecture/Data_Model.md` (tabla §4.3 + nota de diseño nueva)
  - `_DevLog/_index.md` (fila nueva + corrección BUG-008→BUG-009 en la fila del 22-ago)
  - `_DevLog/2026-08-23-diana-alvarez-dec009-grano-cubos.md` (este archivo)
- **Decisiones autónomas del agente:** ninguna de fondo — la decisión de grano es de Diana; el
  agente investigó evidencia real (SQL ya mergeada, docs canónicos) antes de recomendar, y esperó
  su confirmación explícita antes de escribir DEC-009.
- **Correcciones manuales:** ninguna.
- **Prompt inicial:** revisión de tres mensajes de Teams sobre posibles bloqueantes, para decidir
  qué avanzar.

## Seguridad / calidad
- [x] Cambio de esquema (regla 7) — revisión humana explícita de Diana (Tech Lead Célula 1),
      con evidencia verificada antes de confirmar, no solo aceptada de palabra
- [x] DevLog enlaza a los IDs afectados (DEC-009, DEC-008, REQ-002, US-113, US-211b, US-203)
- Pendiente de Diana: correr `vault_lint.py` y `pytest tests/ -q` antes de pushear este cambio,
  igual que en el PR #74

## Próximos pasos
- Diana: commitear y pushear `Decision_Log.md`, `Data_Model.md`, `_DevLog/_index.md` y este
  DevLog desde una rama nueva, y abrir PR.
- Avisar a Deni y Monserrat por Teams (mensaje ya redactado y enviado en sesión).
- Deni continúa materializando US-113 con el grano confirmado.