---
project: "FARO"
date: "2026-08-14"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión única: US-211a — contrato semántico de los cubos de DB-03 y DB-04"
touches: ["US-211a", "REQ-002", "DOC-CUBESPEC-DB0304", "DOC-TRACE-MATRIX", "MOC-04", "SPRINT-MARINA-GARCIA-DEL-BUEY"]
tags: [devlog, bi, cubos, capa-semantica, celula-2]
---

# DevLog — 2026-08-14 — US-211a: contrato semántico de los cubos de DB-03 y DB-04

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

Primera sesión de trabajo de Marina en el repositorio. US-211a es su primera historia (S3, 17–23 ago);
se arranca 3 días antes porque US-113 (construcción de los cubos, Deni Garrido, C1) corre **el mismo
sprint** y necesita esta especificación como insumo: si C1 materializa los cubos sin ella, hay retrabajo.

Punto de partida: [[vault/03_Architecture/Data_Model]] §4.3 declara el **grano** de `cubo_escuela_360` y
`cubo_comparador_municipio` pero **no sus columnas**, y [[vault/04_UX_Design/Screen_Specs]] cataloga KPI-01…KPI-14
sin ningún KPI propio de DB-03. Ese hueco es justo el alcance de US-211a.

## Qué se hizo

- **`vault/04_UX_Design/Cube_Specs_DB03_DB04.md`** (nuevo, `DOC-CUBESPEC-DB0304`): contrato semántico completo
  — granos, llaves, catálogo de métricas, jerarquías y rutas de drill-down, mapeo a los KPIs canónicos,
  contrato de dependencias con C1/C3 y solicitudes formales a otras células.
- **`superset/semantic/`** (nuevo): `db03_cubo_escuela_360.sql`, `db04_cubo_comparador_municipio.sql`,
  `metrics_db03_db04.yaml` y `README.md`. Los `.sql` tienen doble uso: dataset virtual de Superset para
  US-212 y **SQL de referencia para US-113**.
- **`tests/test_semantic_db03_db04.py`** (nuevo): 28 casos que convierten las reglas del proyecto en algo
  que el CI hace cumplir — `SIN_DATO` nunca es cero, salidas de ML solo por `JOIN`, umbral 0.6, grano y
  filtros globales. Validación estática, sin base de datos ni dependencias nuevas.
- **Trazabilidad:** fila de REQ-002 en [[vault/02_Requirements/Traceability_Matrix]] (arquitectura, test, DevLog,
  estado 📋 → 🟡), alta en [[vault/04_UX_Design/_index]] y §9 del plan de sprint.

## Decisiones de modelado (revisadas y aceptadas por la humana)

1. **`LEFT JOIN` a las salidas de ML en el grano de escuela.** Los KPI agregados de Manuel usan `JOIN`
   interno porque miden poblaciones ya puntuadas; la ficha de DB-03 no puede hacerlo: con `JOIN` interno,
   una escuela sin predicción **desaparecería del tablero sin explicación** — un nulo silencioso a nivel
   de fila. Se une con `LEFT` y se expone `cobertura_prediccion` / `cobertura_recomendacion`.
   La regla de lectura (salidas de ML por `JOIN`) **no cambia**; solo se fija el tipo de `JOIN`.
2. **Componentes aditivos en vez de promedios precalculados en DB-04.** Un promedio no se puede
   reagregar: si el cubo guardara `indice_riesgo_promedio`, al quitar el filtro de nivel Superset
   promediaría promedios y daría un número incorrecto. Se guardan numerador y denominador por separado
   y la razón vive en la capa semántica, con las mismas fórmulas de KPI-02 y KPI-03.
3. **Los promedios de driver excluyen `SIN_DATO`** y publican su denominador real (`escuelas_con_d#`).
   `pct_escuelas_en_riesgo` divide entre escuelas **con predicción**, no entre el total: decir "10% en
   riesgo" cuando solo se puntuó al 30% inventaría una cobertura que no existe.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:**
  - `vault/04_UX_Design/Cube_Specs_DB03_DB04.md` (nuevo)
  - `superset/semantic/db03_cubo_escuela_360.sql` (nuevo)
  - `superset/semantic/db04_cubo_comparador_municipio.sql` (nuevo)
  - `superset/semantic/metrics_db03_db04.yaml` (nuevo)
  - `superset/semantic/README.md` (nuevo)
  - `tests/test_semantic_db03_db04.py` (nuevo)
  - `vault/02_Requirements/Traceability_Matrix.md`
  - `vault/04_UX_Design/_index.md`
  - `vault/12_Roadmap_Sprints/Sprints/2-marina-garcia-del-buey.md`
  - `vault/_DevLog/2026-08-14-marina-garcia-cubos-db03-db04.md` (nuevo) · `vault/_DevLog/_index.md`
- **Decisiones autónomas del agente:** ninguna sobre alcance. Las tres decisiones de modelado de arriba
  se plantearon y se aceptaron antes de escribir código; el reparto de KPIs (proponer a Manuel en vez de
  editar su catálogo) lo decidió la humana.
- **Prompt inicial:** confirmar si US-211a es lo primero que toca a Marina y, si sí, ejecutarla sin salirse
  de su alcance.
- **Frenos aplicados por el agente:** no se tocó `dbt/` (la materialización de los cubos es US-113 de C1),
  ni `vault/03_Architecture/Data_Model.md` (dueña: Diana), ni `vault/04_UX_Design/Screen_Specs.md` (dueño: Manuel),
  ni `vault/_Meta/` (PM). Todo eso quedó como **solicitud formal** en §8 del contrato.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Tests agregados: `tests/test_semantic_db03_db04.py` — 28 casos ✅ (`pytest tests/ -q`: 93 passed, 4 skipped)
- [x] `python vault/_Meta/scripts/vault_lint.py .` → ✅ Vault limpio
- [x] DevLog enlaza a los IDs afectados
- [x] Sin datos reales: la validación es estática, no toca `data/raw/` ni fixtures nuevos

## Hallazgos del ambiente local (reportados, no todos resueltos)

- **Python 3.12.10 en local vs 3.11 en CI** y en `CLAUDE.md`. Pendiente: recrear el venv con 3.11.
- **`docker compose ps` vacío**: ningún servicio arriba. No bloquea US-211a; sí bloquea US-212.
- `pip install -r requirements.txt` estaba desactualizado en el venv (faltaban `fastapi`, `uvicorn`,
  `scikit-learn`) → reinstalado; la suite completa pasa.
- **`requirements/celula-2.txt` no existe** (sí las de C1/C3/C4/C5). Queda pendiente al instalar Superset.
- **Bug reportado al PM:** `vault/_Meta/scripts/vault_lint.py` truena con `UnicodeEncodeError` al imprimir la
  sección de huérfanos en consolas Windows (cp1252). El vault **sí** queda limpio (exit 0). Workaround:
  `$env:PYTHONIOENCODING="utf-8"`. `vault/_Meta/**` está fuera del alcance de Marina: **no se corrigió**.

## Bloqueantes

- Ninguno para US-211a. Para **US-212** (S4) se necesita `gold.*` (US-112/US-113, Deni) y Superset
  levantado.

## Pendiente de coordinación (no editado por Marina)

- **Diana Alvarez (C1):** cambio de grano de `cubo_comparador_municipio` a `municipio × nivel × ciclo`
  — sin `nivel` en el grano, **AC-002.2 no se puede cumplir en DB-04**. Cambio de esquema ⇒ regla 7.
  También, confirmar la codificación de `SIN_DATO` en `d1`…`d6` (§8.2 del contrato).
- **Manuel Serranía (C2):** alta de **KPI-15…KPI-18** para DB-03 en su catálogo (AC-002.4 los exige y hoy
  no existen), ratificación del `LEFT JOIN` y adopción de `superset/semantic/` en US-202.
- **Deni Garrido (C1):** recibir el SQL de referencia **antes** de materializar los cubos en US-113.
- **PM:** `DEC-005` (umbral 0.6) sigue sin registrarse en [[vault/10_Risk_Governance/Decision_Log]]; el log llega
  a DEC-004. Además, el bloque "Estado del proyecto" de la matriz reporta 1/7 REQ con Test, cifra ya
  desactualizada (la consolida el PM).

## Próximos pasos

- PR desde `feat/marina-buey-cubos-db03-db04` → revisión de Manuel (compuerta técnica) → PM (DEC-003).
- Levantar Docker y congelar `requirements/celula-2.txt` con el stack de Superset.
- **US-212 (S4):** construir DB-03 y DB-04 sobre estos datasets.
