---
project: "FARO"
date: "2026-08-22"
author_human: "Monserrat Xcaret Miranda Olivas"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión corta: correcciones de la revisión de Manuel (PR #73) + registro de DEC-009"
touches: ["US-211b", "REQ-002", "DOC-CUBESPEC-DB0508", "DEC-009"]
tags: [devlog, bi, cubos, capa-semantica, celula-2, fix]
---

# DevLog — 2026-08-22 — Correcciones de revisión (Manuel) y cierre de §8.1 (Diana/DEC-009) — US-211b

## Qué se hizo

Seguimiento del PR #73 (US-211b) tras la revisión de los dueños de área:

- **Diana Álvarez aceptó §8.1** (cambio de grano de `cubo_driver`), registrado como **DEC-009**
  (extiende el criterio a los 4 cubos nuevos del sprint, no solo el de Monserrat). No requirió
  cambios de código: el SQL ya traía el grano propuesto.
- **Manuel Serranía dejó "Requested Changes" en el PR** con 2 correcciones bloqueantes:
  1. **Bug real de doble escalado** en `pct_escuelas_sin_dato`: la expresión SQL multiplicaba por
     100 *y* el formato `porcentaje_1` (d3 `%`) también multiplica por 100 al mostrar — resultado
     "3,180.0%" en vez de "31.8%". Corregido: se quitó el `* 100.0` de
     `superset/semantic/metrics_db05_db08.yaml`.
  2. Checklist del PR con casillas sin marcar — pendiente de limpiar en la descripción del PR
     (fuera del repo, vía GitHub).
- Aprobó §8.3 (KPI-19/KPI-20 y formato largo como convención).
- Se agregó `test_ninguna_metrica_porcentaje_duplica_el_escalado` (sugerencia no-bloqueante de
  Manuel) a `tests/test_semantic_db05_db08.py` para prevenir este tipo de bug a futuro.
- `Cube_Specs_DB05_DB08.md` §8.1 y §8.3 actualizados a ✅ resuelto; `status` del frontmatter pasa
  de `in_review` a `approved`.

## 🤖 Sesión de IA

Archivos tocados: `superset/semantic/metrics_db05_db08.yaml`, `superset/semantic/db05_cubo_driver.sql`
(comentario de cabecera), `tests/test_semantic_db05_db08.py`, `04_UX_Design/Cube_Specs_DB05_DB08.md`.
Decisión autónoma: ninguna de fondo — ambas correcciones fueron indicadas explícitamente por
Manuel en su revisión; el agente solo las aplicó y las verificó con pruebas.

## Seguridad/calidad

- [x] `pytest tests/test_semantic_db05_db08.py -v` → 30 passed (antes 29; +1 por la prueba nueva).
- [x] `pytest tests/ -q` → 298 passed, 4 skipped.
- [x] `python _Meta/scripts/vault_lint.py .` → ✅ Vault limpio.
- [x] DevLog enlaza IDs tocados.

## Bloqueantes

- Ninguno de fondo. Pendiente: limpiar el checklist de la descripción del PR en GitHub (Monserrat)
  y esperar la aprobación obligatoria de Edgar (CODEOWNERS/DEC-003).

## Próximos pasos

1. Push del fix a la rama del PR #73.
2. Actualizar el checklist de la descripción del PR (fuera del repo).
3. Solicitar que Manuel re-revise (o marque como resuelto) tras el fix.
