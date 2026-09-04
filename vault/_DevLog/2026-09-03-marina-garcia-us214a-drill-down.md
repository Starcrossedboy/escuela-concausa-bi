---
project: "FARO"
date: "2026-09-03"
author_human: "Marina García del Buey"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "sesión larga: reconstrucción del ambiente local desde cero + US-214a"
touches: ["US-214a", "US-212", "US-211a", "REQ-002", "AC-002.2", "AC-002.4", "BUG-037", "BUG-012", "ADR-007", "DEC-008"]
tags: [devlog, bi, dashboards, superset, drill-down, celula-2]
---

# DevLog — 2026-09-03 — US-214a: filtros y drill-down cruzado en DB-03 y DB-04

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/04_UX_Design/Cube_Specs_DB03_DB04]] §8.bis

## Contexto

Primera sesión sobre la estructura nueva del repositorio (rama fija `dev/marina-garcia`,
`ownership.yml` como padrón que hace cumplir el CI). Dos objetivos: dejar el ambiente local
corriendo la versión actual, y cerrar US-214a.

## Ambiente local reconstruido desde cero

La base local estaba en la versión anterior: **ninguna tabla `gold.cubo_*` existía**, que es
justo de donde leen los datasets de DB-03/DB-04 desde el repunteo de US-205. Se bajó el stack
con sus volúmenes (verificado antes: solo contenía fixtures, 242/182/72/72/12 filas) y se
reconstruyó. La cadena completa, en orden:

1. `docker compose down -v` + `build superset` + `up -d db superset`
2. Los **tres** fixtures de Formato 911 a `bronze.formato911_2024_2025` (242 filas)
3. Siete fixtures de drivers (CCT, CEMABE, CONEVAL, CONAPO, SESNSP, SINAICA ×2)
4. `python superset/cargar_geojson_municipios.py` → 317 geometrías
5. `dbt seed` → `gold.dim_driver`
6. `dbt run --full-refresh` → estrella completa, `features_escuela` **145 filas, 3 ciclos**
7. `publicar_gold --desde-gold` → **55 predicciones + 55 recomendaciones**, ML-01 MAE 0.0818
8. `dbt run --select "gold.cubo_*"` → **8 de 9 cubos**
9. `sync_semantic_layer.py --validar-datos` → **103 charts con datos, 9 tableros**

Las cifras coinciden con la reproducción de Héctor Morales del mismo día (145 / 3 ciclos /
55 / 55), que es la comprobación de que el ambiente quedó equivalente y no "parecido".

### Verificación de números, no de que corra

**ADR-007 está implementado punta a punta.** `gold.predicciones.valor` sale en rango
`−0.0437 … +0.0313`: es **fracción**, no alumnos absolutos. Y el `indice_riesgo` va de
`0.1637` a `0.5615` — ya no está saturado, que era el síntoma de BUG-017.

**AC-002.4 ya se puede verificar**, que era lo único que faltaba para cerrar US-212: 55
escuelas con `cobertura_prediccion = OK` y 90 con `SIN_DATO` (los ciclos sin predicción).
Los bloques ML de DB-03 renderizan con datos reales.

**KPI-02 por tres caminos independientes** (BUG-031):

| Origen | Matrícula | Anterior | KPI-02 |
|---|---|---|---|
| `gold.fact_escuela_ciclo` | 32 312 | 32 374 | −0.192 % |
| DB-03 · `cubo_escuela_360` | 32 312 | 32 374 | −0.192 % |
| DB-04 · `cubo_comparador_municipio` | 32 312 | 32 374 | −0.192 % |

Son los mismos valores verificados el 29-ago. La tarjeta restituida de DB-04 concuerda.

**Regla `SIN_DATO`:** D1 145/145, D5 145/145, D6 140/145, D3/D4 12/145, D2 0/145, y **cero
casos** donde un driver marcado `SIN_DATO` traiga valor.

## US-214a — qué se construyó

**AC-002.2 ya estaba cubierto**: ambos tableros tenían sus filtros de ciclo, entidad y nivel
desde US-212. Lo que faltaba era la **navegación cruzada**, declarada en el bloque
`drill_down:` desde US-211a y nunca implementada.

Se implementaron las **dos rutas cuyo origen vive en esta historia**:

- `link_db04` en `db03_cubo_escuela_360.sql` — desde una escuela, a su municipio
- `link_db03` en `db04_cubo_comparador_municipio.sql` — desde un municipio, a sus escuelas

Mecanismo reusado de US-214b (Monserrat): `<a href>` con `native_filters` en RISON más
`allow_render_html: true`. Superset no tiene navegación entre tableros — el cross-filtering
y el Drill to Detail nativos operan solo dentro del mismo tablero, y SIP-77 fue rechazada.

Se agregó el filtro `cve_mun` **al final** de `filtros_globales` en ambos tableros (índice 4).
Al final a propósito: los IDs de filtro se generan por posición, así que insertar en medio
corre los índices y rompe la navegación sin ningún error visible.

### Corrección de contrato encontrada al implementar

`DB-04 → DB-03` estaba declarada con llave **`cct`**, y es **imposible**: DEC-008 fijó el
grano de ese cubo en `[cve_mun, nivel, id_ciclo]` y no tiene columna `cct`. Corregida a
`cve_mun`. El contrato ahora lleva `estado` por ruta (`implementado` / `bloqueado` / `ajeno`),
para que la brecha entre lo declarado y lo construido se lea sin abrir el código.

### Rutas que no se pudieron construir

- `DB-03 → DB-06` y `DB-03 → DB-09`: **DB-06 y DB-09 no exponen filtro `cct`**. Sin él, el
  link aterriza en el tablero completo en vez de en la escuela, que es justo lo que la ruta
  promete. Se necesita que **Manuel Serranía** (US-204) agregue `cct` al final de los
  `filtros_globales` de ambos. No se shippea un link que no hace lo que dice.
- `DB-01 → DB-03`, `DB-02 → DB-03`, `DB-02 → DB-04`: el link vive en el SQL de origen, que es
  de Manuel. Para `DB-02 → DB-04` el destino **ya quedó listo** (filtro `cve_mun`, índice 4).

## Cómo se probó

`tests/test_drill_down_db03_db04.py` (nuevo, 18 casos). Cada guarda se validó
**reintroduciendo el defecto a propósito** — falla con él y pasa sin él:

| Defecto reintroducido | ¿Lo cazó? |
|---|---|
| Mover `cve_mun` del índice 4 al 0 en DB-04 | ✅ 2 casos |
| Quitar `allow_render_html` del chart de DB-03 | ✅ |
| Devolver la llave imposible `cct` a `DB-04 → DB-03` | ✅ *(a la segunda, ver abajo)* |
| Quitar el `%27` del quoting RISON | ✅ |

**La primera versión de la prueba de llaves no servía.** Buscaba la llave en el texto crudo
del SQL y pasaba con `cct`, porque la palabra aparece en el comentario que explica por qué
`cct` es imposible. Es la misma clase de falla que BUG-027 —una prueba que parece correcta y
no prueba nada— y el repo ya tenía el helper `sin_comentarios()` justo para eso. Corregida.

Verificación **contra el Superset desplegado**, que ninguna prueba estática puede hacer: se
decodificó el RISON con `prison` (la misma librería que usa Superset) y se contrastó cada
`NATIVE_FILTER-US203-{i}` contra `native_filter_configuration` del tablero real. Los cuatro
destinos correctos.

Suite completa: **858 passed, 7 skipped** · `vault_lint.py` ✅ · `ruff` ✅.

## Hallazgos reportados

- **BUG-037 se reprodujo exactamente**: al agregar `link_db04`/`link_db03` los charts
  reventaron con `Columns missing in dataset`. El sync actualiza el SQL del dataset pero no
  vuelve a leer sus columnas, y el error **solo aparece al abrir el tablero**. Mitigado a mano
  con `PUT /api/v1/dataset/<id>/refresh`. El arreglo de fondo toca `sync_semantic_layer.py`,
  herramienta compartida de C2 — requiere acuerdo con Manuel antes de tocarla.
- **CONEVAL (DS-07) no es reproducible desde el repo.** `dbt/models/silver/rezago_municipio.sql`
  espera el esquema del extracto real (columnas hasheadas, p. ej. `c_5d0523b1d4a3` =
  "Índice de rezago social") y `tests/fixtures/bronze_coneval_sample.csv` trae otro esquema.
  No existe fixture compatible. Sin el archivo real de CONEVAL nadie construye
  `silver.rezago_municipio` → `gold.dim_municipio` → **ningún cubo** → **ningún tablero**.
  Se rodeó creando las dos tablas vacías solo en la base local, para que D1 salga `SIN_DATO`
  y no un número inventado. **El arreglo es de Célula 1.**
- **BUG-012 sigue costando.** Cuatro pasos del pipeline no están en ningún runbook: `dbt seed`
  (sin él fallan 6 cubos), el orden ML-antes-de-cubos (sin él fallan 9), las `vars` de
  identificadores para fixtures, y el nombre del target de dbt.
- `docker/init-db.sql` intenta `CREATE EXTENSION postgis` sobre `postgres:15-alpine`, que no
  la trae: error en cada arranque limpio.
- El healthcheck de `db` en `docker-compose.yml` no tiene `start_period`, así que el primer
  `docker compose up` sobre volumen nuevo **siempre** falla con "dependency failed to start".
- `superset/README.md` dice `docker restart faro-superset`, pero los `container_name` se
  quitaron el 29-ago; ahora es `escuela-concausa-bi-superset-1`.

## 🤖 Sesión de IA

- **Agente / modelo:** Claude Code / claude-opus-5
- **Archivos creados/modificados:** `superset/semantic/db03_cubo_escuela_360.sql`,
  `superset/semantic/db04_cubo_comparador_municipio.sql`,
  `superset/semantic/metrics_db03_db04.yaml`,
  `superset/dashboards/db03_ficha_escuela.yaml`,
  `superset/dashboards/db04_comparador_municipio.yaml`,
  `tests/test_drill_down_db03_db04.py` (nuevo),
  `vault/04_UX_Design/Cube_Specs_DB03_DB04.md`, este DevLog, `vault/_DevLog/_index.md`,
  `vault/02_Requirements/Traceability_Matrix.md`
- **Fuera de alcance, no editado:** `dbt/**` y `src/**` (se ejecutaron, no se modificaron).
  `superset/sync_semantic_layer.py` no se tocó pese a que BUG-037 lo justifica: es herramienta
  compartida de C2 y el arreglo se acuerda con Manuel.
- **Decisiones autónomas del agente:** reusar el patrón de US-214b en vez de investigar de
  cero; agregar `cve_mun` al final y no en medio; **no** shippear las rutas a DB-06/DB-09 por
  no tener destino válido.
- **Correcciones manuales:** la prueba de llaves se reescribió tras comprobar que no cazaba
  el defecto que decía cazar.
- **Manejo de secretos:** no se escribieron credenciales en ningún formulario; la validación
  contra Superset se hizo por API leyendo las variables del `.env` del ambiente.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] Tests agregados (18 casos nuevos), cada guarda validada reintroduciendo su defecto
- [x] `vault_lint.py` ✅ · `ruff` ✅ · suite completa en verde
- [x] DevLog enlaza a los IDs afectados
- [x] Datos: solo fixtures del repo (≤500 filas, anonimizados); ninguna descarga real

## Bloqueantes

- **Manuel Serranía (C2):** filtro `cct` en `db06_predicciones.yaml` y
  `db09_recomendaciones.yaml` para las dos rutas restantes de DB-03.
- **Manuel Serranía (C2):** acuerdo para arreglar BUG-037 en `sync_semantic_layer.py`.
- **Célula 1:** fixture de CONEVAL compatible con `rezago_municipio.sql`.

## Próximos pasos

- US-215a: pruebas de usabilidad y accesibilidad de DB-03/DB-04. **Bloqueada por alcance**:
  el plan equivalente de US-215b vive en `vault/06_Quality_Testing/`, y la raíz de esa carpeta
  no está en el alcance de nadie en `ownership.yml`. Requiere decisión del PM.
- US-207: pendiente de acordar alcance con el PM.
