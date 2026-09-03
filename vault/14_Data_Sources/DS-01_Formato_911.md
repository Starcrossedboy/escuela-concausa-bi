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
- **URL de descarga (verificada real, no PENDIENTE):** portal
  [repodatos.atdt.gob.mx](https://repodatos.atdt.gob.mx) (Datos Abiertos SEP, "Registro de
  alumnado y personal docente — educación básica y media superior — Formato 911"). Cada ciclo
  escolar tiene su propia URL de archivo — **no siguen una fórmula derivable** (2023-2024 y
  2024-2025 rompen el patrón de los ciclos anteriores cada una a su manera, verificado a mano
  por Diana, clic derecho → copiar dirección del enlace en datos.gob.mx). Las 6 URLs reales,
  una por ciclo, viven en `SOURCE_URL_POR_CICLO` de
  `src/ingesta/extractor_formato911_historico.py`:
  - 2019-2020: `https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2019-2020.csv`
  - 2020-2021: `https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2020-2021.csv`
  - 2021-2022: `https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2021-2022.csv`
  - 2022-2023: `https://repodatos.atdt.gob.mx/s_educacion_publica/f911/BASICA_2022-2023.csv`
  - 2023-2024: `https://repodatos.atdt.gob.mx/s_educacion_publica/f911/ESTANDAR_BASICA_I2324.csv`
  - 2024-2025: `https://repodatos.atdt.gob.mx/api_update/secretaria_educacion/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/educacion_basica_2024_2025.csv`
    (mismo archivo que usa `src/ingesta/extractor_formato911.py`, el cargador de ciclo único de
    PR #105 — es la misma fuente, dos extractores distintos, ver nota de aislamiento en el
    docstring de `extractor_formato911_historico.py`)
- **Formato:** CSV, ~190 columnas reales por archivo (solo se extraen las que hace falta, ver §5).
- **Tamaño real:** no medido en MB (son CSV de texto plano vía HTTP directo, no ZIP) — conteo de
  filas real por ciclo confirmado en §9 (228,804–231,913 filas según ciclo).
- **Distribución alterna — serie SNIEE:** la SEP publica esta **misma fuente ya agregada** a nivel
  `municipio × nivel` como serie **multi-año** (SNIEE / Sistema de Consulta de Estadística Educativa,
  planeacion.sep.gob.mx — URL PENDIENTE-CONFIRMAR, sitio caído por DNS al momento de intentar
  acceder, ver §9a). **No es una 9ª fuente**, es DS-01 en otra distribución. Es la vía que
  habilitaría el target real multi-año por `DEC-007` como alternativa — **no bloqueante**: el
  target ya se calcula del microdato real del 911 (ver §9a, decisión tomada con el equipo).

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

### Camino A — reproducir la carga real, ahora automatizado (2026-09-03, verificado en vivo)
Actualización 2026-09-03: se automatizó la descarga real de DS-02 y del histórico DS-01 (antes
había que bajar los archivos a mano). `src/ingesta/extractor_cct.py` llama a la API real que usa
el propio portal SIGED tras inspeccionar su JS en vivo (nunca se inventó ninguna URL — ver
docstring del módulo y DevLog 2026-09-03), con las cabeceras y la sesión que hace falta para que
la API no corte la conexión (User-Agent/Referer/Origin de navegador, reintento con backoff y
pausa entre las 2 partes — verificado real, la API tolera 1 llamada pero cortaba la conexión sin
pausa entre 2 seguidas).

1. Levantar Postgres local: `docker compose up -d` (servicio `db`, ver `docker-compose.yml`,
   dueño Luis Téllez/C5) — o cualquier Postgres 15 local propio.
2. Un solo comando para DS-02 (catálogo CCT) + DS-01 histórico (6 ciclos):
   ```bash
   python -m src.ingesta.reproducir_bronze_real
   ```
   Orquesta `cargar_bronze_cct_automatico` (DS-02, vía `extractor_cct.py`) y
   `cargar_bronze_formato911_historico_real` (DS-01, los 6 ciclos) en el orden correcto —
   ambos idempotentes (`ON CONFLICT DO NOTHING`), así que correrlo de nuevo no duplica nada,
   solo reporta "0 filas nuevas". Verificado real 2026-09-03: corrida limpia de punta a punta,
   385,204 filas en `bronze.cct_siged_202608` + ~1.37M filas en `bronze.formato911_historico`
   (6 ciclos), sin intervención manual.
   - **No incluye** `bronze.formato911_2024_2025` (ciclo único, PR #105) — viene de un portal
     distinto sin extractor automatizado todavía; si hace falta, se sigue cargando a mano:
     `python -m src.ingesta.cargar_bronze_formato911_real --csv ... --ciclo 2024-2025`.
3. `dbt run` **completo** (no solo `--select`) y luego `dbt test`. Importante: dbt materializa
   tablas, no vistas vivas — un `ref()` no se recalcula solo, hay que correr el DAG explícito
   tras cargar Bronze nuevo (visto en vivo 2026-09-03, ver DevLog de esa fecha).
- **Tiempo estimado:** minutos, no horas (antes el cuello de botella real era la descarga manual
  de 250+196 MB de DS-02 más 6 ciclos de DS-01 — con el comando único ya no hace falta bajar
  nada a mano).

### Camino B — restaurar el dump de Bronze de Diana (minutos, no horas)
Más rápido porque salta la descarga. **Dump ya generado** (2026-09-03,
`bronze_real_2026-09-03.dump`, 33 MB, todo el schema `bronze` real) — pendiente solo de que
Diana lo suba al canal de Teams del equipo y comparta el link (nunca por git: CLAUDE.md "Nunca
subas datos reales pesados"; `data/raw/` está en `.gitignore` por la misma razón, y `*.dump`
también se agregó al `.gitignore` como candado extra).

```bash
# Ya generado por Diana:
pg_dump -h localhost -U postgres -d escuela_concausa_db -n bronze -Fc \
  -f bronze_real_2026-09-03.dump

# Cualquiera lo restaura en su propio Postgres local (vacío, recién creado), una vez que
# Diana lo comparta por Teams:
pg_restore -h localhost -U postgres -d escuela_concausa_db --no-owner --no-privileges \
  bronze_real_2026-09-03.dump

# Y luego, igual que en el Camino A:
dbt run && dbt test
```
Incluye `bronze.formato911_historico` (~1.37M filas reales, 6 ciclos, verificado 2026-09-03),
`bronze.cct_siged_202608` (385,175 filas, verificado 2026-09-03 contra `silver.escuela` sin
duplicados) y `bronze.formato911_2024_2025` (ciclo único, PR #105). No incluye Silver/Gold: esos
se recalculan localmente con `dbt run`, para que el pipeline de cada quien se siga ejerciendo de
verdad.

> Esto resuelve el bloqueador de *ambiente* (Camino A siempre disponible, Camino B en cuanto
> Diana genere y comparta el dump). La deuda de Great Expectations para DS-01/DS-02 -- que
> seguia aparte -- se cierra en la misma sesion, ver SS12.

## 12. Calidad de datos (Great Expectations) -- 2026-09-03

Suite nueva para la distribucion HISTORICA de Bronze (`bronze.formato911_historico`), cerrando
la deuda senalada por Deni Garrido en su auditoria del 30-ago (ver DevLog
2026-08-30-diana-alvarez-ds02-cct-real, seccion Pendiente).

- **Modulo:** `src/ingesta/validacion_formato911_historico.py` (`validar_formato911_historico()`),
  mismo patron que `validacion_sesnsp.py` (TEST-011/US-124b): corre sobre el Parquet mas
  reciente de `data/bronze/formato911_historico/`, o sobre un DataFrame explicito.
- **Expectativas:** not_null en columnas criticas, formato real de `cct`/`entidad`/`municipio`
  (verificado contra `tests/fixtures/bronze_formato911_historico_sample.csv`), formato de
  `ciclo` (`AAAA-AAAA`, sin fijar los 6 ciclos actuales -- la fuente sigue publicando ciclos
  nuevos), `matricula_total >= 0`. **No** valida unicidad de `(cct, ciclo, turno)` a proposito
  -- Bronze permite reingestas legitimas del mismo cct+ciclo+turno con `_ingested_at` mas nuevo
  (ver UNIQUE real de la tabla); esa reingesta la dedupea Silver por turno
  (`matricula_historica.sql`). Tampoco valida un `value_set` de `nivel` -- Bronze SÍ trae
  valores fuera de educacion basica (p.ej. `INICIAL`, confirmado real 2026-09-03, ver DevLog);
  el filtro a PREESCOLAR/PRIMARIA/SECUNDARIA es responsabilidad de Silver, no de esta suite de
  Bronze.
- **Suite persistida:** `great_expectations/expectations/suite_ds01_formato911_historico.json`.
- **Pruebas offline (5):** `tests/test_validacion_formato911_historico.py` -- datos limpios
  pasan, y se verifica que la suite SÍ atrapa matricula negativa, ciclo mal formado, cct mal
  formado y nulo en columna critica (no solo que corre sin tronar). Corren sin red ni Postgres,
  mismo principio que US-124b.
- **Verificado 2026-09-03 contra los 6 Parquet reales completos** (no la muestra sintetica de
  las pruebas), uno por ciclo: 2019-2020 (230,424 filas), 2020-2021 (228,852), 2021-2022
  (228,804), 2022-2023 (229,691), 2023-2024 (231,534), 2024-2025 (231,913) -- los 6 en verde,
  13/13 expectativas cada uno.
