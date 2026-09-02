---
id: RPT-DATOS-BLOQUEO-P01-2026-09-01
title: "Qué falta para el recálculo de producción-local (P-01/P-02) — Carril A, corte 1-sep-2026"
owner: "Luis Téllez Domínguez"
status: active
source_of_truth: false
traces_up:
  - "vault/14_Data_Sources/_index"
  - "vault/12_Roadmap_Sprints/Execution_Status"
traces_down:
  - "vault/14_Data_Sources/DS-03_CEMABE"
last_reviewed: "2026-09-01"
tags: [report, data-sources, blocker, carril-a, handoff, pm]
---

# Qué falta para el recálculo de producción-local — Carril A, 1-sep-2026

> El **recálculo de producción sobre Postgres local** (renglón 10 del Carril A: `publicar_gold
> --desde-gold`) está bloqueado por **P-01** (las 8 fuentes reales) y su hijo **P-02** (CEMABE).
> La causa es **una sola**: faltan URLs de descarga que **no se pueden inventar** (regla dura del
> proyecto). Este documento deja escrito *qué* falta y *quién* lo destraba — no pide trabajo a la
> capa de datos, que ya está lista, sino que quita el obstáculo de dato.
> → [[vault/14_Data_Sources/_index]] · [[vault/13_Reports/US_Pendientes_Cierre_2026-08-30]]

## Resumen — quién destraba

| Bloqueo | Fuentes | Quién destraba |
|---|---|---|
| **URL de descarga sin confirmar** | DS-02, DS-03, DS-08 (y verificar DS-06) | Sus dueños: Diana, Deni, Emilio |
| **Parser del archivo real** | DS-03 CEMABE (CSV) | Deni (fuente) + Carril A (parser) |
| **Cargador real a Bronze** | las que no sean DS-01 | Carril A — *una vez que exista la URL* |

**7 de los 10 renglones del Carril A están cerrados** (transformación, drivers, `dim_municipio`,
target, KPI-02, argmax, D2, auditoría de tests). Los 3 que faltan (8, 9, 10) son **capa de
ingesta real**, y todos cuelgan del mismo clavo.

## Regla dura que hay que respetar

> **Las 8 fuentes suben juntas o ninguna** (Carril A §6.9). Cargar solo DS-01 real contra 12
> municipios de CONEVAL deja los otros cinco drivers en `SIN_DATO` y **vacía más** los tableros de
> lo que están hoy. Por eso el renglón 10 **no debe correrse parcial**: es una sola corrida con
> P-01 completo. La guarda `verificar_escala_variacion` (`src/modelos/riesgo.py`) además detendría
> una publicación con el target en la escala equivocada — hace bien.

## Estado por fuente (las 8 · 9 tablas Bronze)

Leído del árbol (`src/ingesta/`, `vault/14_Data_Sources/DS-*.md`) el 1-sep-2026:

| DS | Fuente | Dueño | Extractor | URL real | Cargador real | Qué falta |
|---|---|---|---|---|---|---|
| DS-01 | Formato 911 | Diana | ✅ `extractor_formato911(+_historico)` | ✅ (nota "superado" en ficha) | ✅ `cargar_bronze_formato911_real.py` (en `main`) | **nada** — verificar corrida |
| DS-02 | Catálogo CCT | Diana | ❌ **no existe** | 🔴 `PENDIENTE-CONFIRMAR` | ❌ | **URL + extractor + cargador** |
| DS-03 | CEMABE | **Deni** | ⚠️ `extractor_cemabe.py` degrada seguro | 🔴 `PENDIENTE-CONFIRMAR` | ❌ | **URL + parser CSV + cargador** (=P-02, renglón 8) |
| DS-04 | SESNSP | Luis García | ✅ intocable (§9) | ✅ verificada 2026-08-24 | ⚠️ por confirmar | cargador real a Bronze |
| DS-05 | SINAICA | Luis García | ✅ intocable (§9) | ✅ endpoints confirmados | ⚠️ por confirmar | cargador real a Bronze |
| DS-06 | CONAGUA | **Emilio** | ✅ `extractor_conagua.py` (§9 dice funciona) | ⚠️ ficha dice `PENDIENTE`, código puede tenerla | ❌ | **confirmar URL** (discrepancia ficha↔código) + cargador; D5 sale de `SIN_DATO` |
| DS-07 | CONEVAL | Deni | ✅ `extractor_coneval.py` (resuelto PR #151) | ✅ resuelto #151 | ⚠️ por confirmar | cargador real a Bronze |
| DS-08 | CONAPO | **Emilio** | ✅ `extractor_conapo.py` | 🔴 `PENDIENTE-CONFIRMAR` | ❌ | **URL + cargador** |

Los `⚠️ por confirmar` de cargador son **trabajo de Carril A que no requiere decisión ajena**: el
cargador genérico ya tiene DDL y llave de conflicto para las 9 tablas Bronze (renglón 9), así que
escribir cada cargador real "es alimentar una función que existe" — **pero solo tiene sentido
cuando la URL de esa fuente esté confirmada**, porque hasta entonces no hay de dónde bajar el dato.

## Ruta de desbloqueo (en orden)

1. **Confirmar 3 URLs** (bloqueo duro, no es de la capa de datos):
   - **DS-02 Catálogo CCT → Diana** · **DS-03 CEMABE → Deni** · **DS-08 CONAPO → Emilio**
   - y **verificar DS-06 CONAGUA → Emilio** (la ficha dice pendiente pero §9 afirma que el
     extractor funciona; hay que resolver cuál manda — el código, y actualizar la ficha).
   - Para **DS-03** hace falta además **una muestra del CSV real** para escribir el parser sin
     adivinar la estructura de columnas.
2. **Carril A escribe lo que falta** *(ya con URLs)*: parser de CEMABE, extractor de DS-02 y los
   cargadores reales pendientes, todos sobre el cargador genérico.
3. **Una sola corrida de recálculo** (renglones 5-10 juntos, Carril A §7): foto base → cargar las
   8 fuentes reales → `dbt build` → `publicar_gold.py --desde-gold` **contra Postgres LOCAL** →
   foto final, cada diferencia explicada en una frase.
4. Recién ahí se destraban `gold.predicciones`, `escuelas_en_riesgo` y los `indice_riesgo`.

⚠ **Contra Cloud SQL NO** — eso es promoción y no es del Carril A.

## Lo que YA está listo (no rehacer)

- **Transformación completa**: `fact_escuela_ciclo.sql` y `features_escuela.sql` con
  `matricula_ciclo_anterior`, target en fracción (ADR-007), argmax invertido (`1-d3`/`1-d4`, P-05),
  D2 como tasa ÷ población CONAPO (P-10) y el Haversine acotado por caja ±0.2° (listo para el
  volumen real).
- **`dim_municipio`** = universo INEGI (317), `SIN_DATO` explícito.
- **Auditoría de los 56 tests `dbt/tests/`**: limpia — ninguno codifica el defecto de KPI-02, del
  argmax ni de la escala del target; los dos que tocan esas áreas son guardas que lo *cazan*.
- **Ingesta ya funcional**: cargador genérico + `cargar_bronze_formato911_real.py`; extractores
  SESNSP y SINAICA con URL verificada (intocables, §9); CONEVAL resuelto (#151).

## Qué necesito de cada dueño (accionable)

- **Diana** — URL oficial de descarga de **DS-02 Catálogo CCT** (portal SEP / datos.gob.mx) y visto
  bueno para crear su extractor. (DS-01 ya quedó; solo confirmar que su corrida real está sana.)
- **Deni** — URL oficial de **DS-03 CEMABE** (INEGI/SEP) **+ una muestra del CSV** para el parser.
- **Emilio** — URL oficial de **DS-08 CONAPO** y aclarar el estado real de **DS-06 CONAGUA** (¿el
  extractor ya tiene la URL en código? entonces actualizar la ficha; ¿no? entonces confirmarla).

## Nota de método

- **Leído** (no deducido): el inventario de `src/ingesta/`, las 8 fichas `DS-*.md` (campo *URL de
  descarga*), `extractor_cemabe.py` (`SOURCE_URL="PENDIENTE-CONFIRMAR"` + `TODO` del parser), y los
  dos modelos Gold completos.
- **Deducido**: que a DS-04/05/07 les *podría* faltar el cargador real a Bronze — se ve que solo
  existe el de DS-01; **marcado como "por confirmar"**, no como hecho.
- **Dice un documento** (posible desactualización, §8.3): las fichas `DS-*.md` marcan
  `PENDIENTE-CONFIRMAR` y `status: draft/in_review`; para DS-06 eso **contradice** al Carril A §9
  ("el extractor de CONAGUA funciona"). El código manda; la ficha se actualiza.
