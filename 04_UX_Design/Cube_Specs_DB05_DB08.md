---
id: DOC-CUBESPEC-DB0508
title: "Cube Specs — Contrato semántico de los cubos de DB-05 y DB-08"
owner: "Monserrat Xcaret Miranda Olivas"
status: in_review
version: "1.0"
traces_up: ["DOC-SCREENSPECS", "DOC-DATAMODEL", "US-211b", "REQ-002"]
traces_down: ["US-213", "US-214b", "US-215b"]
last_reviewed: "2026-08-22"
tags: [bi, cubos, capa-semantica, dashboards, celula-2]
---

# Cube Specs — Contrato semántico de DB-05 y DB-08

> Métricas, jerarquías y granos de los cubos que alimentan **DB-05 (Análisis por driver)** y
> **DB-08 (Explorador del cubo)**. Implementa **US-211b** (REQ-002) y es el **insumo formal para
> US-113** (construcción de los cubos, Célula 1).
> → [[04_UX_Design/_index]] · Fuentes canónicas: [[03_Architecture/Data_Model]] · [[04_UX_Design/Screen_Specs]]
> · Plantilla: [[04_UX_Design/Cube_Specs_DB03_DB04]] (US-211a, Marina García del Buey)

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

### 2.1 Decisión de diseño: v1 no lee salidas de ML

A diferencia de los cubos de DB-03/DB-04, `cubo_driver` y `cubo_pivot` analizan el **driver
observado** (`d1`…`d6` de `gold.fact_escuela_ciclo`), no la predicción. No hay `LEFT JOIN` a
`gold.predicciones` ni a `gold.recomendaciones` en ninguno de los dos SQL de este documento. R1
sigue vigente como principio del proyecto — si una iteración futura de DB-05/DB-08 agrega
`indice_riesgo` o `driver_dominante`, tendrá que ser por `LEFT JOIN`, igual que en DB-03.

Nota: **KPI-07** ("Driver dominante — distribución") ya aparece listado contra DB-05 en
[[04_UX_Design/Screen_Specs]] §4, pero se sirve directo de `gold.recomendaciones` + `dim_driver` —
no depende de `cubo_driver`. Queda como pregunta abierta a Manuel (§8.3) si US-213 debe absorber
ese chart dentro de `cubo_driver` o dejarlo como está.

### 2.2 Decisión de diseño: formato largo (unpivot), no columnas `d1..d6`

Ambos cubos guardan **una fila por driver** (`id_driver` como columna, D1…D6 apilados vía
`UNION ALL`), no columnas `d1`…`d6` como en `fact_escuela_ciclo`. Es el mismo patrón que ya usa
KPI-06 del catálogo canónico. Es lo que permite que DB-05 muestre "un tab por driver" (US-213) con
**un solo juego de charts** filtrado por `id_driver`, en vez de 6 charts casi duplicados por
columna.

**Riesgo y mitigación — doble conteo.** Columnas como `escuelas`, `suma_valor` o `matricula_total`
se **repiten una vez por cada driver** dentro del mismo municipio/escuela × ciclo. Sumarlas sin
agrupar/filtrar por `id_driver` las multiplica ×6: si un municipio × nivel × ciclo tiene 40
escuelas, `SUM(escuelas)` sin filtrar por driver da 240, no 40. Por eso cada dataset del YAML
declara `dimension_obligatoria_en_agregacion: id_driver`, y un test estático
(`tests/test_semantic_db05_db08.py`) lo verifica, no solo la prosa de este documento.

---

## 3. `gold.cubo_driver` — DB-05 Análisis por driver

### 3.1 Grano y llaves

| | |
|---|---|
| **Grano propuesto** | una fila por **`id_driver` × `cve_mun` × `nivel` × `id_ciclo`** |
| **Grano en el esquema canónico hoy** | `driver × municipio × ciclo` ([[03_Architecture/Data_Model]] §4.3) — **sin `nivel`** |
| **Llave primaria** | (`id_driver`, `cve_mun`, `nivel`, `id_ciclo`) |
| **Banderas de cobertura** | `cobertura_driver` (una sola bandera: el formato largo ya separa cada driver en su propia fila) |
| **Alimenta** | DB-05 (distribución de los 6 drivers y su evolución) |

> 🔴 **Cambio de grano solicitado a la Célula 1 — ver §8.1.** El grano canónico (`driver ×
> municipio × ciclo`) **no puede satisfacer AC-002.2**: si el cubo se pre-agrega sin `nivel`, el
> filtro global de nivel educativo no tiene sobre qué operar en DB-05. Misma solución que DEC-008
> aplicó a DB-04: bajar un nivel el grano y reagregar con métricas aditivas.

### 3.2 Columnas del cubo

**Identidad y contexto** (dimensiones conformadas, no se agregan):

| Columna | Tipo | Origen | Uso en DB-05 |
|---|---|---|---|
| `id_driver` | str (`D1`…`D6`) | `dim_driver` | Selector de tab (US-213) |
| `nombre_driver` | str | `dim_driver.nombre` | Etiqueta legible del tab |
| `fuente_driver` | str | `dim_driver.fuente` | Nota de fuente en el tab |
| `driver_nivel_geografico` | str | `dim_driver.nivel_geografico` | Aclara si el driver se mide a nivel municipio o escuela — **no confundir con el filtro `nivel` educativo** |
| `cve_mun` / `cve_ent` | str | `fact_escuela_ciclo` / `dim_municipio` | **Filtro global de entidad** |
| `nombre_municipio` / `nombre_entidad` | str | `dim_municipio` | Migas de pan |
| `nivel` | str | `dim_escuela` | **Filtro global de nivel** |
| `id_ciclo` / `ciclo` / `anio_inicio` | str/int | `dim_tiempo` | Filtro global de ciclo · eje de la evolución |

**Componentes aditivos** (§2.2 explica por qué son componentes y no un promedio):

| Columna | Tipo | Definición |
|---|---|---|
| `escuelas` | int | `COUNT(DISTINCT cct)` en ese municipio × nivel × ciclo — **repetida ×6, una vez por driver** |
| `suma_valor` | float | `SUM(valor)` **solo sobre `cobertura = 'OK'`** |
| `escuelas_con_dato` | int | `COUNT(*)` sobre `cobertura = 'OK'` — denominador real |
| `cobertura_driver` | enum `OK`/`SIN_DATO` | `SIN_DATO` cuando `escuelas_con_dato = 0` |

### 3.3 Catálogo de drivers: fuente, ADR y estado real (22-ago-2026)

| Driver | Nombre | Fuente | Nivel de medición | Estado real (`fact_escuela_ciclo.sql`) | ADR |
|---|---|---|---|---|---|
| D1 | Pobreza | CONEVAL (DS-07) | municipio | Real | — |
| D2 | Inseguridad | SESNSP (DS-04) | municipio | Real | — |
| D3 | Infraestructura | CEMABE (DS-03) | escuela | Real | [[03_Architecture/ADRs/ADR-005-dim-driver-mapeo]] |
| D4 | Conectividad | CEMABE (DS-03) | escuela | Real | [[03_Architecture/ADRs/ADR-005-dim-driver-mapeo]] |
| D5 | Agua | CONAGUA SINA (DS-06) | escuela (IDW, radio 15km) | **`SIN_DATO` 100%** — sin `bronze.conagua` real todavía | [[03_Architecture/ADRs/ADR-006-idw-calidad-aire-agua]] |
| D6 | Aire (PM2.5) | SINAICA (DS-05) | escuela (IDW, radio 15km) | Real | [[03_Architecture/ADRs/ADR-006-idw-calidad-aire-agua]] |

> La fila D5 en DB-05 mostrará `cobertura_driver = 'SIN_DATO'` en el 100% de las combinaciones
> hasta que Emilio Galnares Ruiz (DS-06) entregue datos reales de CONAGUA. **No es un bug** — es R2
> funcionando correctamente. El tablero debe decirlo explícitamente, nunca "arreglarlo" con
> `COALESCE(d5, 0)`.

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
| Propuesta | **DB-05** | DB-08 | `(cve_mun, id_driver)` | ⬜ Propuesta, para US-214b |

### 3.5 Métricas derivadas (capa semántica de Superset)

Ver §5 para el mapeo completo a KPIs. Fórmulas en `superset/semantic/metrics_db05_db08.yaml`.

### 3.6 Cuidado con el doble conteo en formato largo

Ejemplo: si un municipio × nivel × ciclo tiene 40 escuelas, `SUM(escuelas)` **sin** agrupar/filtrar
por `id_driver` da 240 (40 × 6 drivers), no 40. Regla operativa: **todo chart de este dataset debe
traer `id_driver` en el filtro o en el group-by.** Ver §2.2.

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

| Métrica del cubo | KPI | Cubo |
|---|---|---|
| `valor_promedio_driver` | **KPI-19** (propuesto) | `cubo_driver` |
| `pct_escuelas_sin_dato` | **KPI-06** (reusado — dueño formal DB-07) | `cubo_driver` |
| `valor_driver` | **KPI-20** (propuesto) | `cubo_pivot` |

### 5.1 KPI-19 y KPI-20 — propuestos aquí, pendientes de publicación por Manuel

El catálogo va de KPI-01 a KPI-18 (verificado: KPI-19 y KPI-20 están libres) y **ningún KPI está
asignado hoy a DB-05 ni DB-08** — mismo vacío que tuvo DB-03 antes de que Marina propusiera
KPI-15…18 (ver [[04_UX_Design/Cube_Specs_DB03_DB04]] §5.1). Se proponen dos altas para que Manuel
las incorpore a [[04_UX_Design/Screen_Specs]] (documento canónico suyo — regla 1 del vault):

| ID propuesto | KPI | Grano | Expresión | Sustenta |
|---|---|---|---|---|
| **KPI-19** | Valor promedio y evolución del driver | `id_driver × cve_mun × nivel × id_ciclo` | `SUM(suma_valor) / NULLIF(SUM(escuelas_con_dato), 0)`, agrupado por `id_driver`; la evolución agrupa además por `anio_inicio` | Screen_Specs §2 (DB-05: "distribución de los 6 drivers y su evolución") · AC-002.2 · AC-002.5 |
| **KPI-20** | Valor del driver por escuela (exploración libre) | `cct × id_driver × id_ciclo` | Sin agregación — alimenta el pivote libre | Screen_Specs §2 (DB-08: "pivotable y drill-down libre sobre el hecho") |

> **Nota honesta:** a diferencia de DB-03 (AC-002.4 dedicada), no existe hoy una AC específica para
> DB-05/DB-08 en `Requirements_Detailed.md` — solo las generales AC-002.1/.2/.5. Se registra como
> observación, no se inventa una AC nueva.

Texto de la solicitud formal a Manuel: ver §8.3.

---

## 6. SQL de referencia — entregable para US-113 (Célula 1)

El SQL vive en `superset/semantic/` para poder usarse también como **dataset virtual** de Superset
mientras los cubos físicos no existan:

- `superset/semantic/db05_cubo_driver.sql`
- `superset/semantic/db08_cubo_pivot.sql`

Son **propuestas de implementación**, no código de producción: la materialización (`dbt`, índices,
estrategia de refresco) es decisión de la Célula 1 en US-113.

Índices sugeridos a C1:

| Cubo | Índice sugerido | Motivo |
|---|---|---|
| `cubo_driver` | `(id_driver, cve_mun, nivel, id_ciclo)` único · `(id_driver, id_ciclo)` | Filtro por tab de driver (US-213) + serie de tiempo |
| `cubo_pivot` | `(cct, id_driver, id_ciclo)` único · `(id_driver, cve_mun, id_ciclo)` | Pivote libre por escuela y por geografía |

---

## 7. Contrato de dependencias

| Columna(s) | Depende de | Historia | Estado hoy (22-ago) |
|---|---|---|---|
| `fact_escuela_ciclo`, `dim_escuela`, `dim_municipio`, `dim_tiempo`, `dim_driver` | Célula 1 · Gold | US-103/104/105 | ✅ Materializado y validado (19-ago) |
| `gold.cubo_driver`, `gold.cubo_pivot` (físicos) | Célula 1 · Gold | US-113 | ⬜ No existe ningún `cubo_*.sql` en `dbt/models/gold/` (mismo estado que DB-03/DB-04) |
| D5 (agua) real | Célula 1 · DS-06 (Emilio Galnares Ruiz) | US-105 / DS-06 | ⬜ `SIN_DATO` 100%, sin `bronze.conagua` |
| Salidas de ML | — | — | **No aplica a v1** (§2.1) |

**Comportamiento mientras las dependencias no llegan:** D5 muestra `cobertura_driver = 'SIN_DATO'`
explícito (§3.3). El tablero no se rompe ni miente con ceros.

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
- **Estado:** 🟡 Solicitud enviada el 2026-08-22. **No bloquea US-211b.**

### 8.2 A Diana Alvarez (C1) — nota, no solicitud

`cubo_pivot` (DB-08) **no** necesita cambio de grano: su grano `cct × driver × ciclo` ya trae
`nivel` gratis vía `dim_escuela`, igual que `cubo_escuela_360` (DB-03) tampoco lo necesitó. Se deja
registrado para que quede claro por qué solo §8.1 pide un cambio.

### 8.3 A Manuel Serranía (C2) — pendiente

> Hola Manuel — cerrando US-211b (cubos de DB-05 y DB-08). Dos cosas para que las ratifiques en el
> catálogo, mismo proceso que seguiste con KPI-15…18 de Marina:
>
> 1. Propongo **KPI-19** (Valor promedio y evolución del driver — grano `driver × municipio ×
>    nivel × ciclo`, alimenta DB-05) y **KPI-20** (Valor del driver por escuela — grano `cct ×
>    driver × ciclo`, alimenta DB-08). Verifiqué que ambos IDs están libres (el catálogo llega a
>    KPI-18). El % de escuelas sin dato del driver reusa **KPI-06** (dueño DB-07) — no inventé un
>    ID ahí.
> 2. Para que DB-05 muestre "un tab por driver" (US-213) sin duplicar 6 juegos de charts, modelé
>    ambos cubos en **formato largo** (unpivot: una fila por driver, no columnas `d1..d6`) — mismo
>    patrón que ya usa KPI-06. ¿Lo ratificamos como convención válida para cubos analíticos nuevos,
>    junto al formato ancho que ya usan DB-03/DB-04?
>
> Detalle completo en §5 y aquí mismo. Nota aparte, no bloqueante: ¿`cubo_driver` debería absorber
> KPI-07 (driver dominante) para DB-05, o lo dejamos sirviéndose directo de
> `gold.recomendaciones` como hoy?
>
> Ninguna de las dos cosas me bloquea para abrir el PR hoy — las marco como pendientes y sigo.

| Solicitud | Estado |
|---|---|
| Alta de KPI-19 y KPI-20 en el catálogo (§5.1) | ⬜ pendiente |
| Ratificar el **formato largo** como patrón aceptado para cubos analíticos nuevos | ⬜ pendiente |
| Confirmar si `cubo_driver` debe absorber KPI-07 (driver dominante) | ⬜ pendiente, no bloquea |

**Estado:** 🟡 Solicitud enviada el 2026-08-22.

---

## 9. Trazabilidad

- **Implementa:** US-211b (REQ-002)
- **Consume:** [[03_Architecture/Data_Model]] §4 · [[04_UX_Design/Screen_Specs]] §2, §4 ·
  `dbt/seeds/dim_driver.csv` · [[03_Architecture/ADRs/ADR-005-dim-driver-mapeo]] · [[03_Architecture/ADRs/ADR-006-idw-calidad-aire-agua]]
- **Alimenta:** US-213 (construcción de DB-05/DB-08), US-214b (filtros y drill-down), US-215b
  (usabilidad)
- **Insumo para:** US-113 (construcción de los cubos, Célula 1)
- **Sustenta AC:** AC-002.1, AC-002.2, AC-002.5
