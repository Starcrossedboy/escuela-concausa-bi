---
id: DS-01
title: "DS-01 · SEP Formato 911"
owner: "Diana Aracely Alvarez Varela"
status: done
traces_up: ["vault/01_Product/PRD", "vault/12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, hecho-central]
---

# DS-01 · SEP Formato 911

> → [[vault/14_Data_Sources/_index]] · **PR #105 mergeado (28-ago-2026)** — cargador real de producción en `main`, 6 ciclos (2019-2020 a 2024-2025), 149/149 tests dbt en verde. Target calculado del microdato del 911 (no de SNIEE, sitio caído por DNS — ver §9a)

## 1. Identificación
- **Nombre oficial:** Estadística Educativa — Formato 911.
- **Institución responsable:** SEP (Secretaría de Educación Pública), vía SIGED / datos.gob.mx.
- **Qué aporta al proyecto:** matrícula, docentes y grupos **por CCT y ciclo escolar**. Es el
  **hecho central** del proyecto (`fact_escuela_ciclo`). Unidad de observación = ESCUELA, nunca el
  alumno (privacidad por diseño).

## 2. Acceso
- **URL de descarga:** PENDIENTE-CONFIRMAR (portal esperado: SIGED / datos.gob.mx).
- **Formato:** CSV / XLSX.
- **Tamaño aproximado:** PENDIENTE-CONFIRMAR.
- **Distribución alterna — serie SNIEE:** la SEP publica esta **misma fuente ya agregada** a nivel
  `municipio × nivel` como serie **multi-año** (SNIEE / Sistema de Consulta de Estadística Educativa,
  planeacion.sep.gob.mx — URL PENDIENTE-CONFIRMAR). **No es una 9ª fuente**, es DS-01 en otra
  distribución. Es la vía que habilita el **target real multi-año** por `DEC-007` sin reconstruir años
  crudos del 911 (el 911 crudo aporta el desglose por escuela para features y driver dominante).

## 3. Frecuencia real de actualización
- **Anual**, por ciclo escolar (inicio de cursos).

## 4. Cobertura geográfica y temporal
- **Geográfica:** Nacional.
- **Temporal:** serie desde el ciclo **1990-91** (confirmar disponibilidad de años recientes en la
  prueba de descarga).

## 5. Esquema esperado (confirmar en prueba de descarga)
| Columna | Tipo | Nota |
|---|---|---|
| `cct` | str (10) | Clave de Centro de Trabajo — llave |
| `ciclo` | str | Ciclo escolar, p. ej. `2023-2024` |
| `entidad` | str (2) | Clave INEGI de entidad |
| `municipio` | str (3/5) | Clave de municipio |
| `nivel` | str | Nivel educativo |
| `alumnos_total` | int | Matrícula total |
| `docentes_total` | int | Plantilla docente |
| `grupos_total` | int | Número de grupos |

## 6. Llave de unión
- **CCT** (escuela). Deriva **clave INEGI de 5 dígitos** (entidad+municipio) para cruces municipales.

## 7. Driver que alimenta
- Ninguno directamente: **es el hecho central (matrícula)** sobre el que se calculan el riesgo y la
  variación. Todos los drivers se cruzan contra este hecho.

## 8. Licencia de uso
- Términos de Libre Uso MX (datos.gob.mx) — **confirmar** en la ficha oficial.

## 9. Prueba de descarga real — 6 ciclos cerrados (ver detalle 2026-08-22)
- [x] Archivo descargado físicamente — **6 ciclos reales** (2019-2020, 2020-2021, 2021-2022,
  2022-2023, 2023-2024, 2024-2025), ver DevLog 2026-08-21/22
- [x] Abierto y con datos utilizables
- [x] Registros contados: 230,424 / 228,852 / 228,804 / 229,691 / 231,534 / 231,913 filas
  (2019-2020 / 2020-2021 / 2021-2022 / 2022-2023 / 2023-2024 / 2024-2025) — 0 filas con
  `matricula_total` no numérico en ninguno de los 6
- [x] Esquema verificado (columnas y tipos) — los 6 parsean con `_parsear_ciclo` sin adivinar nada
- [x] Llave confirmada: CCT presente y válido (`clave_cct`/`clavecct` según ciclo, ver extractor) en
  los 6 ciclos
- [ ] **Serie SNIEE municipio×nivel descargada** — sitio caído por falla de DNS al intentar
  acceder, no bloqueante: se decidió calcular el target del microdato del 911 en su lugar (ver
  §9a)
- **Responsable:** Diana Aracely Alvarez Varela · **Fecha:** 2026-08-21/22

### 9a. Intento 2026-08-22 (a petición de Edgar) — resultado

- **2º ciclo crudo (2023-2024):** ~~el entorno cloud de esta sesión no tiene salida general a
  internet, pendiente reintentar desde una máquina con internet real~~ — **superado**: Diana
  descargó y validó los 6 ciclos completos (incluido 2023-2024) desde su propia máquina, ver §9.
- **Serie SNIEE municipio×nivel:** el sitio `snie.sep.gob.mx` estaba caído por **falla de DNS** al
  momento de intentar acceder — no se pudo confirmar si la serie existe ahí o no, solo que el sitio
  no resolvía. Se revisaron también `planeacion.sep.gob.mx` y `siged.sep.gob.mx` (sí accesibles),
  más descubrimiento orgánico (Atlas de servicios educativos por estado, Principales Cifras,
  tabulados de INEGI), y ninguno expone esa serie a nivel municipio×nivel×ciclo. Lo público y
  descargable en bloque que sí existe en esos dos portales es a nivel **entidad** (serie histórica
  1990-91→2030-31,
  [`serie_historica_entidades_sep.xlsm`](https://www.planeacion.sep.gob.mx/Doc/estadistica_e_indicadores/serie_historica_entidades_sep.xlsm) /
  [`.zip`](https://www.planeacion.sep.gob.mx/Doc/estadistica_e_indicadores/serie_historica_entidades_sep.zip)).
  El Atlas por estado (ej.
  [Estado de México](https://planeacion.sep.gob.mx/Doc/Atlas_estados/estado_de_mexico.pdf)) sí
  desagrega por municipio, pero son indicadores de infraestructura/censo (agua, luz, internet,
  asistencia escolar por edad), **no matrícula por nivel educativo**.
  **Decisión tomada con el equipo (Héctor y Edgar, por Teams): en vez de esperar a que
  `snie.sep.gob.mx` vuelva a resolver, se calcula el target directamente del microdato real del
  911 multi-ciclo** (6 ciclos, ver §9) — `gold.matricula_municipio_nivel` es el `serie_target` que
  consume `unir_target(..., validate="one_to_one")` de Héctor (PR #56). Pendiente reintentar el
  acceso a `snie.sep.gob.mx` más adelante, por si el DNS se restablece, como vía adicional a
  futuro (no bloqueante).

> Trazas: [[vault/10_Risk_Governance/Decision_Log]] (`DEC-007`) · [[vault/10_Risk_Governance/Risk_Register]] (RISK-007)
> · [[vault/02_Requirements/User_Stories]] (US-104)

## 10. Riesgos conocidos
- Cambios de esquema entre ciclos (columnas que se renombran o desaparecen).
- Codificación/acentos inconsistentes en campos de texto.
- Posible desfase de publicación del ciclo más reciente.
- CCT con formato heterogéneo entre entregas (ceros a la izquierda).
## 11. Bloqueador de equipo — nadie más tiene Bronze real cargado (2026-09-03)

Edgar reportó que, salvo Diana, nadie del equipo tiene un ambiente local con Bronze real
cargado — bloquea validación con datos reales de `gold.cubo_pipeline` (DB-10, Oscar), y de
US-222/US-223/US-224 (Oscar, PR #192). Dos caminos para resolverlo, documentados aquí para que
cualquiera pueda auto-atenderse sin depender de una sesión en vivo con Diana:

### Camino A — reproducir la carga real (mismo proceso que ya corrió Diana)
1. Levantar Postgres local: `docker compose up -d` (servicio `db`, ver `docker-compose.yml`,
   dueño Luis Téllez/C5) — o cualquier Postgres 15 local propio.
2. Descargar a mano los archivos reales:
   - DS-01 (6 ciclos): URLs en `SOURCE_URL_POR_CICLO` de
     `src/ingesta/cargar_bronze_formato911_real.py`.
   - DS-02 (catálogo CCT, 2 archivos SIGED entidades 01-16/17-32): ver
     [[vault/_DevLog/2026-08-30-diana-alvarez-ds02-cct-real|DevLog 2026-08-30]].
3. Cargar en este orden (cada script es idempotente, `ON CONFLICT DO NOTHING`):
   1. `python -m src.ingesta.cargar_bronze_cct_real ...` (DS-02 — llave que usan los demás)
   2. `python -m src.ingesta.cargar_bronze_formato911_real --csv ... --ciclo 2024-2025` (DS-01,
      ciclo único, PR #105)
   3. `python -m src.ingesta.cargar_bronze_formato911_historico_real` (DS-01, los 6 ciclos —
      alimenta `target_hibrido.py`, ver nota de esta sesión abajo)
4. `dbt run` **completo** (no solo `--select`) y luego `dbt test`. Importante: dbt materializa
   tablas, no vistas vivas — un `ref()` no se recalcula solo, hay que correr el DAG explícito
   tras cargar Bronze nuevo (visto en vivo 2026-09-03, ver DevLog de esa fecha).
- **Tiempo estimado:** de un par de horas (descargas: 250+196 MB de DS-02, ~230k filas × 6
  ciclos de DS-01) — es la razón real por la que nadie más lo ha hecho todavía, no falta de
  instrucciones.

### Camino B — restaurar el dump de Bronze de Diana (minutos, no horas)
Más rápido porque salta la descarga. Pendiente de ejecutar por Diana (no se puede correr desde
esta sesión de IA — sin acceso de red al Postgres local de nadie):

```bash
# Diana genera el dump (solo el schema bronze, formato custom comprimido):
pg_dump -h localhost -U postgres -d escuela_concausa_db -n bronze -Fc \
  -f bronze_real_2026-09-03.dump

# Lo comparte por Drive/Teams del equipo -- NUNCA por git (CLAUDE.md: "Nunca subas datos
# reales pesados"; data/raw/ está en .gitignore por la misma razón).

# Cualquiera lo restaura en su propio Postgres local (vacío, recién creado):
pg_restore -h localhost -U postgres -d escuela_concausa_db --no-owner --no-privileges \
  bronze_real_2026-09-03.dump

# Y luego, igual que en el Camino A:
dbt run && dbt test
```
Incluye `bronze.formato911_historico` (~1.37M filas reales, 6 ciclos, verificado 2026-09-03) y
`bronze.cct_siged_202608` (385,175 filas, verificado 2026-09-03 contra `silver.escuela` sin
duplicados). No incluye Silver/Gold: esos se recalculan localmente con `dbt run`, para que el
pipeline de cada quien se siga ejerciendo de verdad.

> Esto resuelve el bloqueador de *ambiente* (Camino A siempre disponible, Camino B en cuanto
> Diana genere y comparta el dump). No resuelve la deuda de Great Expectations para DS-01/DS-02,
> que sigue aparte (ver §9, no bloqueante).
