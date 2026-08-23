---
project: "FARO"
date: "2026-08-23"
author_human: "Manuel Alejandro Serrania Reinada"
agent: "OpenCode"
model: "ox-alpha"
type: devlog
session_duration: "~1.5h"
touches: ["US-211b", "US-203", "REQ-002", "KPI-19", "KPI-20", "DOC-CUBESPEC-DB0508", "PR-73", "PR-71"]
tags: [devlog, review, kpis, celula-2, screen-specs]
---

# 2026-08-23 — Manuel Serranía · Primer review de PR (US-211b) + alta de KPI-19/20

## Qué se hizo

### 1. Review del PR #73 (Monserrat Miranda · US-211b, cubos DB-05/DB-08)

Primer review formal como Tech Lead C2. Verificación en local (worktree de su rama):
`test_semantic_db05_db08.py` 29 passed · suite completa **297 passed, 4 skipped** sin regresiones
sobre US-203 · `vault_lint.py` ✅ — sus claims del PR body son ciertos.

**Veredicto: Request Changes**, con dos puntos accionables:

1. 🔴 **Doble escalado de %**: `pct_escuelas_sin_dato` lleva `* 100.0` en la expresión y
   `formato: porcentaje_1`. El sync mapea ese formato a d3 `,.1%` (multiplica ×100 al pintar)
   → mostraría "3,180.0%" en vez de "31.8%". Misma clase del bug "3,181.8%" corregido en la
   sesión 2 de US-203. Convención vigente: razones puras; el `%` lo pone el formato d3.
2. 🔴 Check `quality-checks` en rojo: casillas `[ ]` literales sin marcar en el body del PR.

Y en el mismo comentario se concedió el **§8.3**: KPI-19/KPI-20 ratificados + formato largo
(unpivot) ratificado como convención válida para cubos analíticos nuevos. También se respondió
su consulta no bloqueante: KPI-07 sigue sirviéndose directo de `gold.recomendaciones`
(separación R1: driver observado vs salida ML-02).

Hallazgo de proceso: **nadie tiene test-guarda contra `\*100` en expresiones porcentuales**
(ni siquiera nosotros). Sugerido a Monserrat; pendiente agregarlo también a
`tests/test_semantic_db01_db02.py`.

### 2. Alta de KPI-19 y KPI-20 en el catálogo canónico (`Screen_Specs.md` §4)

- Verificado que los IDs están libres: el catálogo llegaba a KPI-18.
- Fichas agregadas con fórmula SQL **probada contra Postgres local**:
  - **KPI-19 · Valor promedio del driver** — grano `driver × municipio × nivel × ciclo`,
    alimenta DB-05 desde `gold.cubo_driver`. Razón pura `SUM(suma_valor)/SUM(escuelas_con_dato)`
    con bandera `cobertura_driver` (SIN_DATO nunca cero).
  - **KPI-20 · Valor del driver por escuela (exploración)** — grano `cct × driver × ciclo`,
    alimenta DB-08 desde `gold.cubo_pivot`; `AVG(valor_driver)` al grano del detalle
    (no es promedio de promedios; AVG ignora NULL nativamente).
- Ambas fichas usan formato largo (unpivot UNION ALL), consistente con KPI-06 y con los SQL
  reales de `superset/semantic/db05_cubo_driver.sql` / `db08_cubo_pivot.sql`.
- Nota de doble conteo ×6 documentada en la ficha KPI-19.
- `last_reviewed` del frontmatter actualizado a 2026-08-23.

## Verificación

- Consultas de ambas fichas ejecutadas contra Postgres local: D5/agua = SIN_DATO (0 escuelas),
  D6/aire cobertura parcial — comportamiento esperado ✅
- `vault_lint.py` → ✅ Vault limpio

## Notas / riesgos

- El PR #73 queda esperando que Monserrat corrija los 2 puntos; segundo round de review después.
- Pendiente nuestro: test-guarda anti-`*100` para `test_semantic_db01_db02.py` (lo sugirimos a
  ella; aplicarlo también en casa).
- El fallo del contenedor `faro-postgres` detenido al iniciar la sesión confirma que conviene
  revisar healthchecks/restart policies con C5 (ya había antecedente: BUG-006).
