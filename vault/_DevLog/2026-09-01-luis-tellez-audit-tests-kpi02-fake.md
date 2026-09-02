---
project: "FARO"
date: "2026-09-01"
author_human: "Luis Téllez Domínguez"
agent: "Claude Code"
model: "claude-opus-4-8"
session_duration: "1 sesión — item 8 PROMPT-B: barrido de tests/ por el patrón KPI-02; hallazgo único en fixtures_gold.py"
touches: ["BUG-031", "US-411", "REQ-004"]
tags: [devlog, qa, tests, kpi02, bug031, carril-b]
---

# DevLog — 2026-09-01 — Barrido de `tests/` por el patrón KPI-02 (item 8)

→ [[vault/_DevLog/_index|Volver al índice]]

## Contexto

Item 8 y último de la remediación (PROMPT-B §6.8): barrer los **50 archivos** en la raíz de
`tests/` (la lista decía 47; creció) buscando el patrón de BUG-031 — pruebas que **exijan** la
columna pre-agregada de KPI-02 (`variacion_x_matricula`) o que **codifiquen a mano la forma que el
defecto produce** (el producto crudo `SUM(variacion_matricula * matricula_total)`, el promedio
ponderado de una razón, o los valores −54.5%/−0.19%). "De ahí ya salieron tres".

## Método

Primero fijé la **forma exacta del defecto** leyendo los dos DevLogs de BUG-031 (Marina/C2 y
Diana/C1) y el repo real ya corregido en el item 3: KPI-02 es
`SUM(matricula_total) / NULLIF(SUM(matricula_ciclo_anterior), 0) - 1` (razón de sumas), no el
promedio ponderado que pintaba −54.5%. Luego barrí `tests/` por firmas: `variacion_x_matricula`,
`variacion_ponderada`, el producto `* matricula_total`, los valores hardcodeados (−54.5, 287) y
`matricula_ciclo_anterior`. Cada coincidencia se **leyó completa** (§8.1), no se concluyó del grep.

## Qué encontró el barrido

- **Las tres que "ya salieron" están corregidas y son guardas**, no encoders: `test_semantic_db01_db02.py`
  y `test_semantic_db06_db09.py` ahora **afirman lo contrario** (que `suma_matricula_anterior` esté
  presente y `variacion_x_matricula` **no** reaparezca), y `test_semantic_db03_db04.py` suma
  `test_una_metrica_de_porcentaje_no_multiplica_dos_medidas`, un regex que rechaza `SUM(a*b)` en
  métricas de porcentaje. `test_kpis_us221.py` corre el SQL corregido y exige la razón en [−1, 1].
  Nada que tocar ahí.
- **Falsos positivos descartados** (leídos): `target_variacion_matricula` en `test_publicar_gold.py`,
  `test_target_hibrido.py`, `test_entrenar_ml03.py` es el **target de ML** (fracción legítima, ADR-007),
  no el KPI; los `287` y `−0.19` en `tests/fixtures/**` son datos coincidentes (matrícula CONAPO,
  columna target del mock). Todos son Carril A además.

## El hallazgo real (uno): `tests/fixtures_gold.py`

`RepositorioGoldFake.obtener_kpis()` (líneas 242-245 antes) calculaba KPI-02 como
`sum(variacion_matricula * matricula_total) / sum(matricula_total)` — **exactamente el promedio
ponderado que BUG-031 mató**, y sin la columna `matricula_ciclo_anterior`. Este fake es el doble en
memoria de `src/api/repositorio_gold.py` que se inyecta en `tests/test_api_contract.py` para correr
`/kpis` sin Postgres; su docstring dice implementar "el mismo contrato que `RepositorioGoldPostgres`"
—y no lo hacía—. No lo cazó nadie porque **no es un archivo `test_*`** (los barridos anteriores
miraban pruebas, no fixtures) y porque **ninguna aserción toca el valor**: `test_kpis_ok` solo
verifica `status 200` y `escuelas_en_riesgo >= 0`, y los datos-fracción del fake dejaban el promedio
ponderado casualmente dentro de [−1, 1], así que el defecto pasaba silencioso.

**Fix (mismo defecto, un PR):** el fake ahora calcula KPI-02 como **razón de sumas idéntica al repo
real** — `sum(matricula_total) / sum(matricula_ciclo_anterior) - 1`, con el guard sobre
`suma_anterior` reflejando el `NULLIF(...,0)`. Añadí `matricula_ciclo_anterior` a las 5 escuelas
sintéticas y convertí `variacion_matricula` por-escuela a **alumnos absolutos** (`total - anterior`),
como en `gold.fact_escuela_ciclo`, en vez de una fracción. Ese campo no lo expone ningún endpoint
(`_CAMPOS_ESCUELA_OUT` no lo incluye, ningún schema `Out` lo tiene) ni lo asa ninguna prueba, y
`obtener_kpis` ya no lo lee: el fake queda fiel a su contrato y sin la forma del defecto.

## Territorio (lo dejo explícito)

`tests/fixtures_gold.py` **no está literalmente** en la lista §4 (que enumera patrones `test_*.py`),
pero: (1) lo importa **solo** `tests/test_api_contract.py` (mío, `test_api_*`); (2) es el doble de
`src/api/repositorio_gold.py` (mío); (3) fue creado bajo **US-411** (endpoints reales sobre Gold,
repositorio inyectable — trabajo de API/C4, mi carril, acordado con Christian Ruiz TL-C4); (4)
editarlo **no puede chocar con Carril A** (jamás lo tocan). Lo traté como mi superficie de API. No es
`tests/fixtures/**` (ese glob, del Carril A, es el subdirectorio). Queda para que Edgar lo confirme al
mergear.

## Validación (local)

- `ruff check .` (modo estricto, como #165) → **All checks passed!** (exit 0).
- Sanidad del KPI-02 que ahora produce el fake: **+0.140 %** sin filtro, **−2.857 %** con `cve_ent=09`
  — ambos en [−1, 1], como exige `KpisOut.variacion_matricula = Field(ge=-1, le=1)` (schemas.py:136).
- `pytest` de los consumidores (`test_api_contract`, `test_kpis_us221`, los 3 `test_semantic` de
  KPI-02) → **158 passed**.
- **Suite completa** → **453 passed, 4 failed, 5 skipped, 13 errors** — idéntico a la línea base del
  item 7. Los 4 failed (`test_validacion_sesnsp.py`) y los 13 errors de colección son **todos de
  Carril A** y el mismo fallo **ambiental** del venv (`great_expectations…AttributeError`); ninguno
  toca mi territorio ni `fixtures_gold.py`. **Cero regresiones.**
- Cambio **test-only**: el fake no se usa en runtime; el `/api/v1/kpis` real usa el repo ya corregido
  en el item 3. Por eso la verificación correcta es `pytest`, no `curl` al stack.

## Qué necesito del Carril A

Nada. El item 8 cierra la lista §6 completa.

## Fuera de la lista

- **`test_kpis_us221.py:55` es una guarda débil** (*deducido*): solo exige que la razón caiga en
  [−1, 1], rango que el propio promedio ponderado también satisfacía. Cubre la forma "*100" pero no
  la clase "promedio de razones". No la endurecí: el SQL que prueba ya está corregido (item 3) y no
  exige la columna tóxica, así que endurecerla sería reescribir lo que funciona (§9). Lo anoto.
- **Helpers de test sin dueño en §4** (*leído*): `fixtures_gold.py`, `fixtures_modelos.py`,
  `conftest.py` no encajan en ningún patrón `test_*` de la §4. Solo el primero tenía el defecto; los
  otros dos no calculan KPI-02. Vale que la consolidación fije a quién pertenecen los helpers.
