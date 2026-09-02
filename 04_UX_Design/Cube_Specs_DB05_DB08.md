---
id: DOC-CUBESPEC-DB0508
title: "Cube Specs — Contrato semántico de los cubos de DB-05 y DB-08"
owner: "Monserrat Xcaret Miranda Olivas"
status: approved
version: "1.1"
traces_up: ["DOC-SCREENSPECS", "DOC-DATAMODEL", "US-211b", "REQ-002", "US-205"]
traces_down: ["US-213", "US-214b", "US-215b"]
last_reviewed: "2026-08-29"
tags: [bi, cubos, capa-semantica, dashboards, celula-2]
---

# Cube Specs — Contrato semántico de DB-05 y DB-08

> Métricas, jerarquías y granos de los cubos que alimentan **DB-05 (Análisis por driver)** y
> **DB-08 (Explorador del cubo)**. Implementa **US-211b** (REQ-002) y es el **insumo formal para
> US-113** (construcción de los cubos, Célula 1).
> → [[04_UX_Design/_index]] · Fuentes canónicas: [[03_Architecture/Data_Model]] · [[04_UX_Design/Screen_Specs]]
> · Plantilla: [[04_UX_Design/Cube_Specs_DB03_DB04]] (US-211a, Marina García del Buey)

> **v1.1 (2026-08-29, US-205):** DB-05 se **re-escala** para analizar el **driver dominante de
> ML-02** (`gold.cubo_driver`, KPI-07 ratificado) en vez del driver observado `d1..d6`. El KPI-19
> propuesto queda **fuera de v1**; el SQL semántico pasa a hacer `pushthrough` de los cubos
> físicos C1 (repunteo US-113). DB-08 (KPI-20) se conserva observado e intacto.

---

## 1. Alcance y frontera de responsabilidad

| Qué | Quién | Dónde vive |
|---|---|---|
| **Modelar** métricas, jerarquías y granos (este documento) | Monserrat Xcaret Miranda Olivas (C2) | `04_UX_Design/Cube_Specs_DB05_DB08.md` |
| **Materializar** los cubos en Gold (`dbt`) | Deni Garrido Fragoso (C1) · **US-113** | `dbt/` |
| **Esquema canónico** de Gold | Diana Aracely Alvarez Varela (C1) | [[03_Architecture/Data_Model]] |
| **Catálogo canónico de KPIs** | Manuel Alejandro Serranía Reinada (C2) · US-201 | [[04_UX_Design/Screen_Specs]] |
| **Capa semántica de Superset** (convención) | Manuel Alejandro Serranía Reinada (C2) · US-202 | `superset/` |
| **Datasets y métricas de DB-05/DB-08** | Monserrat Xcaret Miranda Olivas (C2) | `superset/semantic/` |

Este documento **no modifica** el esquema canónico. Donde se necesita un cambio en Gold, se registra
como **solicitud a la Célula 1** (§8), nunca como edición de [[03_Architecture/Data_Model]]
(regla 7 del vault: cambio de esquema = revisión humana explícita).

---

## 2. Reglas de modelado heredadas (no negociables)

| # | Regla | Origen |
|---|---|---|
| R1 | **Las salidas de ML se leen siempre por `JOIN`**, nunca como columna del hecho. `indice_riesgo` vive en `gold.predicciones` (`modelo = 'ML-01'`); `driver_dominante`, `recomendacion` y `prioridad` en `gold.recomendaciones`. Se unen por `cct, id_ciclo`. | [[03_Architecture/Data_Model]] §4.1 |
| R2 | **`SIN_DATO` explícito: nunca cero, nunca nulo silencioso.** Prohibido `COALESCE(<driver>, 0)`. Toda métrica de driver viaja con su bandera de cobertura. | [[03_Architecture/Data_Model]] §1 · Screen_Specs P2 |
| R3 | **Umbral de negocio:** "escuela en riesgo" = `indice_riesgo >= 0.6` ≈ perder ~5% de matrícula. | [[15_ML_Models/Indice_Riesgo_ML01]] · ratificado 2026-08-13 |
| R4 | **Llaves:** `cct` (10 caracteres), `cve_mun` (5 dígitos INEGI = `cve_ent`(2) + municipio(3)), `id_ciclo`, `id_driver` (`D1`…`D6`). | [[03_Architecture/Data_Model]] §9 |
| R5 | **Gold acotado** a `SCOPE_ENTIDADES = ["09","15","19","14"]`. El filtro ya viene aplicado desde Gold; los cubos **no** lo repiten. | [[03_Architecture/Data_Model]] §7 |
| R6 | **La escuela es la unidad mínima; jamás el alumno.** Ninguna métrica desagrega por persona. | [[03_Architecture/Data_Model]] §1 |
| R7 | **Filtros globales obligatorios:** ciclo, entidad y nivel educativo, aplicables a *ambos* tableros. | AC-002.2 ([[02_Requirements/Requirements_Detailed]]) |

### 2.1 Decisión de diseño: DB-05 lee ML-02 por cubo; DB-08 sigue observado

**Re-escala de DB-05 (US-205, ratifica §8.3):** DB-05 analiza ahora el **driver dominante de
ML-02** (KPI-07 ratificado) y **ya no el driver observado** (`d1…d6` del hecho → KPI-19 propuesto,
que queda **fuera de v1**). `gold.cubo_driver` fue construido por C1 sobre
`gold_ml_runtime.recomendaciones` y **distingue el 0 real del SIN_DATO**: escuelas a las que
ninguna recomendación asignó ese driver (`escuelas_driver = 0`) vs grupos sin recomendaciones
(`escuelas_driver NULL`, gobernado por `cobertura_recomendacion`). Los dos denominadores reales
(`escuelas_con_recomendacion` / `escuelas_sin_recomendacion`) viajan en el cubo.

R1 sigue vigente: la integración con ML vive **dentro del cubo** (LEFT JOIN en C1), nunca se
copia la salida cruda como columna de un hecho. DB-08 (KPI-20) conserva v1 **observado** — el
explorador pivota el driver medido, no la predicción.

Nota: **KPI-07** ("Driver dominante — distribución") se consolidó como la métrica de DB-05 en el
catálogo canónico ([[04_UX_Design/Screen_Specs]] §4), y la pregunta abierta del §8.3 queda
**resuelta**: DB-05 se sirve de `gold.cubo_driver` (que materializa esa recomendación), no de
`gold.recomendaciones` en crudo.

### 2.2 Decisión de diseño: formato largo (una fila por driver), no columnas `d1..d6`

Ambos datasets guardan **una fila por driver** (`id_driver` como columna), no columnas `d1`…`d6`.
El formato largo ya lo resuelve el cubo físico C1 (que apila D1…D6); la capa semántica lo consume
con `pushthrough`. Es el mismo patrón que ya usa KPI-06/KPI-07 del catálogo canónico. Es lo que
permite que DB-05 muestre "un tab por driver" (US-213) con **un solo juego de charts** filtrado por
`id_driver`, en vez de 6 charts casi duplicados por columna.

**Riesgo y mitigación — doble conteo.** Columnas como `escuelas_por_driver`,
`escuelas_con_recomendacion` o `matricula_total` se **repiten una vez por cada driver** dentro del
mismo municipio/escuela × ciclo. Sumarlas sin agrupar/filtrar por `id_driver` las multiplica ×6: si
un municipio × nivel × ciclo tiene 40 escuelas, `SUM(escuelas_por_driver)` sin filtrar por driver
da 240, no 40. Por eso cada dataset del YAML declara
`dimension_obligatoria_en_agregacion: id_driver`, y un test estático
(`tests/test_semantic_db05_db08.py`) lo verifica, no solo la prosa de este documento.

---

## 3. `gold.cubo_driver` — DB-05 Análisis por driver

### 3.1 Grano y llaves

| | |
|---|---|
| **Grano** | una fila por **`id_driver` × `cve_mun` × `nivel` × `id_ciclo`** — **materializado por C1** (DEC-009 + US-113) |
| **Original solicitado** | `driver × municipio × ciclo` ([[03_Architecture/Data_Model]] §4.3) — **sin `nivel`**, reemplazado por DEC-009 (ver §8.1) |
| **Llave primaria** | (`id_driver`, `cve_mun`, `nivel`, `id_ciclo`) |
| **Banderas de cobertura** | `cobertura_recomendacion` (una sola bandera: el formato largo ya separa cada driver en su propia fila) |
| **Alimenta** | DB-05 (distribución del **driver dominante de ML-02** y su evolución — KPI-07) |

> **Re-escala US-205:** el cubo ya no mide el valor observado del driver (KPI-19 propuesto, fuera de
> v1) sino la **asignación de ML-02** sobre `gold_ml_runtime.recomendaciones` (KPI-07 ratificado).

### 3.2 Columnas del cubo

**Identidad y contexto** (dimensiones conformadas, no se agregan):

| Columna | Tipo | Origen | Uso en DB-05 |
|---|---|---|---|
| `id_driver` | str (`D1`…`D6`) | `dim_driver` | Selector de tab (US-213) |
| `nombre_driver` | str | `dim_driver.nombre` | Etiqueta legible del tab |
| `fuente_driver` | str | `dim_driver.fuente` | Nota de fuente en el tab |
| `driver_nivel_geografico` | str | `dim_driver.nivel_geografico` | Aclara si el driver se mide a nivel municipio o escuela — **no confundir con el filtro `nivel` educativo** |
| `cve_mun` / `cve_ent` | str | `dim_escuela` / `dim_municipio` | **Filtro global de entidad** |
| `nombre_municipio` / `nombre_entidad` | str | `dim_municipio` | Migas de pan |
| `nivel` | str | `dim_escuela` | **Filtro global de nivel** |
| `id_ciclo` / `ciclo` / `anio_inicio` | str/int | `dim_tiempo` | Filtro global de ciclo · eje de la evolución |

**Componentes aditivos** (de ML-02 — el cubo C1 los materializó sobre
`gold_ml_runtime.recomendaciones`; §2.2 explica por qué son componentes y no un promedio):

| Columna | Tipo | Definición |
|---|---|---|
| `total_escuelas` | int | `COUNT(DISTINCT cct)` en ese municipio × nivel × ciclo |
| `escuelas_con_recomendacion` | int | escuelas del grupo que **sí** tienen recomendación ML-02 — denominador real |
| `escuelas_sin_recomendacion` | int | escuelas del grupo **sin** recomendación (laten sin triangulación) |
| `escuelas_driver` | int | escuelas de ese grupo cuyo driver dominante **es** este `id_driver` — `NULL` por combinación sin recomendaciones, nunca 0 inventado (R2) |
| `cobertura_recomendacion` | enum `OK`/`SIN_DATO` | `SIN_DATO` cuando el grupo no tiene recomendaciones |

La capa semántica (`superset/semantic/db05_cubo_driver.sql`) hace `pushthrough` 1:1 de estas
columnas y del catalogo `dim_driver` (enrich vía el cubo); la razón `SUM(escuelas_driver) /
SUM(escuelas_con_recomendacion)` (KPI-07) vive en `metrics_db05_db08.yaml`.

### 3.3 Catálogo de drivers: fuente, ADR y estado real (22-ago-2026)

| Driver | Nombre | Fuente | Nivel de medición | Estado real (`fact_escuela_ciclo.sql`) | ADR |
|---|---|---|---|---|---|
| D1 | Pobreza | CONEVAL (DS-07) | municipio | Real | — |
| D2 | Inseguridad | SESNSP (DS-04) | municipio | Real | — |
| D3 | Infraestructura | CEMABE (DS-03) | escuela | Real | [[03_Architecture/ADRs/ADR-005-dim-driver-mapeo]] |
| D4 | Conectividad | CEMABE (DS-03) | escuela | Real | [[03_Architecture/ADRs/ADR-005-dim-driver-mapeo]] |
| D5 | Agua | CONAGUA SINA (DS-06) | escuela (IDW, radio 15km) | **`SIN_DATO` 100%** — sin `bronze.conagua` real todavía | [[03_Architecture/ADRs/ADR-006-idw-calidad-aire-agua]] |
| D6 | Aire (PM2.5) | SINAICA (DS-05) | escuela (IDW, radio 15km) | Real | [[03_Architecture/ADRs/ADR-006-idw-calidad-aire-agua]] |

> **Re-escala US-205:** DB-05 ya no dibuja el valor observado del driver, sino la **asignación del
> driver dominante por ML-02** (`cobertura_recomendacion`). La disponibilidad real de cada driver
> (D5 «SIN_DATO 100%» hasta que Emilio Galnares Ruiz / DS-06 entregue CONAGUA) es ahora un
> **insumo de ML-02**, no una columna del tablero. Sigue siendo R2 funcionando: nunca se
> «arregla» con `COALESCE(<driver>, 0)`.

### 3.4 Jerarquías y drill-down

```
Entidad (cve_ent)
   └── Municipio (cve_mun)
         └── Nivel educativo         ← grano / filtro global
Driver (id_driver)                   ← selector de tab (US-213), dimensión transversal
Tiempo (anio_inicio → id_ciclo)
```

| Ruta | Desde | Hacia | Llave | Estado |
|---|---|---|---|---|
| Lateral | **DB-05** | DB-07 | `id_driver` | ✅ Ratificada ([[04_UX_Design/Screen_Specs]] §3) |
| Lateral | DB-07 | **DB-05** | `id_driver` | ✅ Ratificada |
| Lateral | **DB-05** | DB-08 | `(cve_mun, id_driver)` | ✅ Ratificada (US-214b, validado en vivo 2026-08-30) |

### 3.5 Métricas derivadas (capa semántica de Superset)

Ver §5 para el mapeo completo a KPIs. Fórmulas en `superset/semantic/metrics_db05_db08.yaml`.

### 3.6 Cuidado con el doble conteo en formato largo

Ejemplo: si un municipio × nivel × ciclo tiene 40 escuelas, `SUM(escuelas_por_driver)` **sin**
agrupar/filtrar por `id_driver` da 240 (40 × 6 drivers), no 40. Regla operativa: **todo chart de
este dataset debe traer `id_driver` en el filtro o en el group-by.** Ver §2.2.

---

## 4. `gold.cubo_pivot` — DB-08 Explorador del cubo

### 4.1 Grano y llaves

| | |
|---|---|
| **Grano** | una fila por **`cct` × `id_driver` × `id_ciclo`** |
| **Grano en el esquema canónico hoy** | `cct × driver × ciclo` ([[03_Architecture/Data_Model]] §4.3) — coincide, **sin cambio de grano** |
| **Llave primaria** | (`cct`, `id_driver`, `id_ciclo`) |
| **Banderas de cobertura** | `cobertura_driver` |
| **Alimenta** | DB-08 (pivotable y drill-down libre sobre el hecho, audiencia "analistas avanzados") |

`nivel` viaja gratis como atributo de `dim_escuela` (vía `cct`), igual que en `cubo_escuela_360`
(DB-03) — por eso este cubo **no** necesita una solicitud de cambio de grano (ver §8.2).

### 4.2 Columnas del cubo

Identidad: `cct`, `nombre_escuela`, `nivel`, `sostenimiento`, `cve_ent`, `cve_mun`,
`nombre_municipio`, `nombre_entidad`, `id_ciclo`/`ciclo`/`anio_inicio`, `id_driver`,
`nombre_driver`, `fuente_driver`, `driver_nivel_geografico`.

Valor: `valor_driver` (float | `NULL`), `cobertura_driver` (`OK`/`SIN_DATO`).

Contexto (repetido ×6 por escuela — ver §2.2): `matricula_total`, `indice_completitud_drivers`.

**Fuera de alcance v1** (extensión propuesta para US-213/US-214b si el producto lo pide): banderas
CEMABE crudas (`agua`, `drenaje`, `electricidad`, `sanitarios`, `internet`, `computadoras`) e
`indice_riesgo`/`recomendacion` (requerirían `LEFT JOIN` a ML, fuera de v1 — §2.1).

### 4.3 Por qué `AVG()` sí es seguro aquí

A diferencia de `cubo_driver` (agregado a municipio), `cubo_pivot` está al **grano de detalle**
(una fila por escuela × driver × ciclo): promediar filas de detalle nunca es "promedio de
promedios", es aritméticamente idéntico a `SUM/COUNT`. Además `AVG()` ignora `NULL` de forma
nativa en SQL, y `valor_driver` es `NULL` exactamente cuando `cobertura_driver = 'SIN_DATO'` —
mismo efecto que excluirlo explícitamente, sin necesitar `FILTER`.

Repite la misma advertencia de doble conteo del §2.2 para `matricula_total` e
`indice_completitud_drivers` (columnas repetidas ×6 aquí; no hay `escuelas`/`suma_valor` en este
cubo).

### 4.4 Jerarquías

- `territorio`: `cve_ent, cve_mun, cct` (igual que DB-03)
- `tiempo`: `anio_inicio, id_ciclo`
- `driver`: `id_driver`
- `oferta`: `nivel, sostenimiento`

---

## 5. Mapeo a los KPIs canónicos

| Métrica del dataset | KPI | Cubo |
|---|---|---|
| `pct_escuelas_por_driver` (y `escuelas_por_driver`) | **KPI-07** (ratificado — driver dominante ML-02) | `cubo_driver` |
| `valor_driver` | **KPI-20** (propuesto v1) | `cubo_pivot` |

> **Re-escala US-205:** el KPI-19 propuesto ("valor promedio del driver observado") queda **fuera
> de DB-05 en v1**; su lugar lo ocupa el KPI-07 oficial del catálogo (driver dominante). KPI-20 se
> mantiene tal cual para DB-08.

### 5.1 KPI-07 (DB-05) y KPI-20 (DB-08)

El catálogo canónico de [[04_UX_Design/Screen_Specs]] asigna **KPI-07** (Driver dominante —
distribución) a DB-05 desde US-204; DB-05 en v1 consume ese KPI vía `gold.cubo_driver`
(decisión US-205, cierra la pregunta abierta del §8.3). Para DB-08 se conserva la propuesta
**KPI-20** (valor del driver por escuela, exploración libre) del formato largo de v1:

| ID | KPI | Grano | Expresión | Sustenta |
|---|---|---|---|---|
| **KPI-07** | Driver dominante — distribución | `id_driver × cve_mun × nivel × id_ciclo` | `SUM(escuelas_driver) / NULLIF(SUM(escuelas_con_recomendacion), 0)`, agrupado por `id_driver` | Screen_Specs §4 (KPI-07) · Screen_Specs §2 (DB-05) |
| **KPI-20** | Valor del driver por escuela (exploración libre) | `cct × id_driver × id_ciclo` | Sin agregación — alimenta el pivote libre | Screen_Specs §2 (DB-08: "pivotable y drill-down libre sobre el hecho") |

> **Nota honesta:** a diferencia de DB-03 (AC-002.4 dedicada), no existe hoy una AC específica para
> DB-05/DB-08 en `Requirements_Detailed.md` — solo las generales AC-002.1/.2/.5. Se registra como
> observación, no se inventa una AC nueva.

---

## 6. SQL en la capa semántica — repunteo a los cubos físicos (US-205)

Los SQL viven en `superset/semantic/` y se usan como **datasets virtuales** de Superset que hacen
`pushthrough` de los cubos físicos C1, más el enrich fino del catálogo `dim_driver`
(junto al repunteo a `gold.cubo_*` de los 13 datasets, US-205):

- `superset/semantic/db05_cubo_driver.sql` → lee `gold.cubo_driver` (ML-02, KPI-07)
- `superset/semantic/db08_cubo_pivot.sql` → lee `gold.cubo_pivot` + `gold.dim_driver` (observado, KPI-20)

La materialización (`dbt`, índices, estrategia de refresco) es de la Célula 1 (US-113). Índices
sugeridos:

| Cubo | Índice sugerido | Motivo |
|---|---|---|
| `cubo_driver` | `(id_driver, cve_mun, nivel, id_ciclo)` único · `(id_driver, id_ciclo)` | Filtro por tab de driver (US-213) + serie de tiempo |
| `cubo_pivot` | `(cct, id_driver, id_ciclo)` único · `(id_driver, cve_mun, id_ciclo)` | Pivote libre por escuela y por geografía |

---

## 7. Contrato de dependencias

| Columna(s) | Depende de | Historia | Estado hoy (29-ago) |
|---|---|---|---|
| `gold.cubo_driver`, `gold.cubo_pivot`, `dim_driver` | Célula 1 · Gold | US-113 | 🔵 **Materializados por C1** (cubos de `gold.cubo_*`, grano DEC-009) — revalidación de datos pendiente del gate de Deni |
| Drivers observados `d1..d6` (hecho) | Célula 1 · Gold | US-103/104/105 | ✅ Materializado y validado (19-ago) — ya **no** alimenta DB-05 en v1 (re-escala US-205) |
| `gold_ml_runtime.recomendaciones` (ML-02) | Célula 3 · `gold.recomendaciones` | US-313 | 🔵 En progreso (mock local MOCK-US203) — `cubo_driver` ya lo consume |
| D5 (agua) real | DS-06 (Emilio Galnares Ruiz) | US-105 / DS-06 | ⬜ `SIN_DATO` 100%, sin `bronze.conagua` — insumo de ML-02 (ver §3.3) |

**Comportamiento mientras las dependencias no llegan:** los grupos sin recomendación de ML-02
muestran `cobertura_recomendacion = 'SIN_DATO'` explícito (§3.2). El tablero no se rompe ni miente
con ceros.

---

## 8. Solicitudes formales a otras células

### 8.1 A Diana Alvarez (C1) — cambio de grano de `cubo_driver`

> Hola Diana — para modelar DB-05 (Análisis por driver) necesito que el grano de
> `gold.cubo_driver` pase de `driver × municipio × ciclo` (como está hoy en `Data_Model.md` §4.3) a
> **`driver × municipio × nivel × ciclo`**, guardando las métricas como componentes aditivos
> (`suma_valor`/`escuelas_con_dato` + `escuelas`) en vez de un promedio precalculado.
>
> **Por qué:** con el grano actual no puedo cumplir AC-002.2 — el filtro global de nivel educativo
> no tendría sobre qué operar en DB-05.
>
> **Precedente directo:** es el mismo tipo de cambio que ya aprobaste para
> `cubo_comparador_municipio` en **DEC-008** (14-ago), para el mismo problema en DB-04.
>
> **Impacto:** cambio de esquema (regla 7 del vault) — necesita tu revisión explícita. Afecta a
> US-113 (Deni) cuando materialice `gold.cubo_driver`.
>
> **No te bloquea nada de mi lado:** ya entregué el SQL de referencia
> (`superset/semantic/db05_cubo_driver.sql`) con el grano propuesto. Si ajustas algo, lo corrijo en
> un PR de seguimiento antes de que US-213 (Sprint 4) consuma el cubo. ¿Me confirmas?

- **Impacto:** cambio de esquema ⇒ **regla 7, revisión humana explícita**. Afecta a US-113 (Deni).
- **Estado:** ✅ **Aceptado por Diana Álvarez el 2026-08-22**, registrado como **DEC-009** (mismo
  formato que DEC-008). Diana extendió el criterio a los 4 cubos nuevos del sprint (`cubo_matricula`,
  `cubo_riesgo_territorial`, `cubo_driver`, `cubo_completitud`) — todos bajan el grano agregando
  `nivel` y guardan las métricas como componentes aditivos. Actualiza `Data_Model.md` §4.3 ella
  misma. `cubo_pivot` confirmado sin cambios (§8.2).

> **v1.1 (US-205):** C1 materializó `gold.cubo_driver` ya bajo la **re-escala a recomendación** —
> los componentes no son `suma_valor`/`escuelas_con_dato` (driver observado) sino
> `escuelas_driver`/`escuelas_con_recomendacion`/`escuelas_sin_recomendacion` + `cobertura_
> recomendacion` (asignación de ML-02). El grano solicitado aquí (con `nivel`) se respetó tal cual.

### 8.2 A Diana Alvarez (C1) — nota, no solicitud

`cubo_pivot` (DB-08) **no** necesita cambio de grano: su grano `cct × driver × ciclo` ya trae
`nivel` gratis vía `dim_escuela`, igual que `cubo_escuela_360` (DB-03) tampoco lo necesitó. Se deja
registrado para que quede claro por qué solo §8.1 pide un cambio.

### 8.3 A Manuel Serranía (C2) — re-escalado a KPI-07 (US-205)

> Versión resuelta: US-211b cerrado (22-ago) — KPI-19 y KPI-20 quedaron pendientes; la re-escala
> US-205 los deja en su lugar definitivo:
>
> 1. **KPI-07** (Driver dominante — distribución, ya oficial en Screen_Specs §4) es a partir de
>    ahora la métrica de **DB-05**, servida por `gold.cubo_driver` que C1 construyó sobre
>    `gold_ml_runtime.recomendaciones` (asignación de ML-02, no valor observado).
> 2. **KPI-19** (Valor promedio del driver observado) queda **fuera de v1** de DB-05.
> 3. **KPI-20** (Valor del driver por escuela) se conserva para DB-08, que sigue observado.
> 4. El **formato largo** queda ratificado como patrón de los datasets por driver; lo materializa
>    el propio cubo y la capa semántica lo consume con `pushthrough`.

| Solicitud | Estado |
|---|---|
| Alta de KPI-19 y KPI-20 en el catálogo (§5.1) | ⬜ **KPI-19 rechazado para DB-05 v1** por la re-escala US-205; ✅ **KPI-20 sigue propuesto para DB-08** |
| Ratificar el **formato largo** como patrón aceptado para cubos analíticos nuevos | ✅ Ratificado |
| Confirmar si `cubo_driver` debe absorber KPI-07 (driver dominante) | ✅ **Resuelto por US-205**: DB-05 = KPI-07 vía `gold.cubo_driver` |

**v1.1 (29-ago):** la re-escala del §2.1 la ejecuta Manuel en US-205 junto con el repunteo de los
13 datasets a `gold.cubo_*`. Las correcciones previas del PR #73 (doble escalado `*100` y checklist)
siguen aplicadas en `metrics_db05_db08.yaml`.

---

## 9. Trazabilidad

- **Implementa:** US-211b (REQ-002)
- **Consume:** [[03_Architecture/Data_Model]] §4 · [[04_UX_Design/Screen_Specs]] §2, §4 ·
  `dbt/seeds/dim_driver.csv` · [[03_Architecture/ADRs/ADR-005-dim-driver-mapeo]] · [[03_Architecture/ADRs/ADR-006-idw-calidad-aire-agua]]
- **Alimenta:** US-213 (construcción de DB-05/DB-08), US-214b (filtros y drill-down), US-215b
  (usabilidad)
- **Insumo para:** US-113 (construcción de los cubos, Célula 1)
- **Sustenta AC:** AC-002.1, AC-002.2, AC-002.5
