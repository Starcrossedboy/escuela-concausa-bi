---
id: DS-02
title: "DS-02 · SEP Catálogo CCT"
owner: "Diana Aracely Alvarez Varela"
status: done
traces_up: ["vault/01_Product/PRD", "vault/12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, llave-primaria]
---

# DS-02 · SEP Catálogo CCT

> → [[vault/14_Data_Sources/_index]] · **PR #163 mergeado (2-sep-2026)** — cargador real de producción en `main`, 77,712 escuelas en `dim_escuela` (4 `SCOPE_ENTIDADES`), verificado Bronze→Silver→Gold contra Postgres real.

## 1. Identificación
- **Nombre oficial:** Catálogo de Centros de Trabajo (CCT).
- **Institución responsable:** SEP.
- **Qué aporta al proyecto:** identidad y **georreferencia** de cada escuela (nombre, nivel,
  sostenimiento, domicilio, lat/lon). Es la **LLAVE PRIMARIA** del proyecto: une todas las fuentes a
  nivel escuela y habilita el cruce municipal.

## 2. Acceso
- **URL de descarga (portal, manual):** [SIGED — Descarga del Catálogo de Centros de
  Trabajo](https://www.siged.sep.gob.mx/SIGED/datos_abiertos.html). El catálogo se publica
  partido por rango de entidad: `CATALOGO_CENTRO_TRABAJO_01_16_CSV.zip` (entidades 01-16) y
  `CATALOGO_CENTRO_TRABAJO_17_32_CSV.zip` (entidades 17-32) — hay que descargar **los dos**;
  de las 4 `SCOPE_ENTIDADES` del proyecto, Nuevo León (19) cae en el segundo. Diccionario de
  datos oficial: `CENTROS_TRABAJO_DICDAT.xlsx` (mismo portal).
- **URL real, automatizada (verificada 2026-09-03):** el portal no expone un link de descarga
  directo — el botón dispara JavaScript (AngularJS, `SIGED/js/tablas_siged.js
  descargarArchivo`) que arma el archivo como Blob en el navegador, sin URL de archivo estática
  que copiar. Se inspeccionó el JS del portal en vivo y se encontró la llamada real que hace:
  `GET https://api.siged.sep.gob.mx/CoreServices/servicios/archivo/buscarArchivos/grupo=CCTS&id={idFile}`
  (`idFile=4` → parte 01-16, `idFile=3` → parte 17-32, verificados en vivo contra el listado
  real de la API — son PK de base de datos, no fórmula, por eso `src/ingesta/extractor_cct.py`
  siempre valida que el `name` que regresa coincide con el esperado antes de aceptarlo). Esta
  URL automatiza Camino A de BLOCK-004 — ver
  [[vault/14_Data_Sources/DS-01_Formato_911|DS-01 §11]].
- **Formato:** CSV, encoding **Latin-1** (no UTF-8 — verificado real, acentos/eñes se corrompen
  si se lee como UTF-8).
- **Tamaño real:** 250.6 MB (01-16, 332,888 filas) + 196.4 MB (17-32, 264,797 filas).

## 3. Frecuencia real de actualización
- **Continua** (el catálogo se actualiza de forma permanente).

## 4. Cobertura geográfica y temporal
- **Geográfica:** Nacional.
- **Temporal:** vigente (estado actual del catálogo); confirmar si hay versiones históricas.

## 5. Esquema real (verificado 30-ago-2026 contra el archivo y el diccionario de datos)
El catálogo real trae 92 columnas con nombres propios de SIGED, no los de este proyecto. El
extractor (`src/ingesta/cargar_bronze_cct_real.py`) traduce solo las que hacen falta:

| Columna del proyecto | Tipo | Columna real en SIGED | Nota |
|---|---|---|---|
| `cct` | str (10) | `CV_CCT` | Llave primaria |
| `nombre` | str | `C_NOMBRE` | Nombre del plantel |
| `nivel` | str | `TIPONIVELSUB_C_SERVICION2` | *(sic, el archivo real dice "SERVICION", no "SERVICIO")*. Filtrado a `PREESCOLAR`/`PRIMARIA`/`SECUNDARIA` |
| `sostenimiento` | str | `SOSTENIMIENTO_C_CONTROL` | `PÚBLICO` / `PRIVADO` |
| `entidad` | str (2) | `INMUEBLE_CV_ENT` | Clave INEGI entidad |
| `municipio` | str (3) | `INMUEBLE_CV_MUN` | Código **local** de 3 dígitos, no la clave INEGI de 5 — `normalize_cve_mun(entidad, municipio)` en `silver/escuela.sql` concatena |
| `latitud` | float | `INMUEBLE_LATITUD` | Georreferencia |
| `longitud` | float | `INMUEBLE_LONGITUD` | Georreferencia |

**Filtro de universo (ambos necesarios):** `C_TIPO == "ESCUELA"` — el catálogo de "Centros de
Trabajo" también incluye supervisiones de zona, bibliotecas, centros de maestros, etc. **OJO:**
`C_TIPO == "ESCUELA"` por sí solo *no* implica educación básica — también incluye
`MEDIA SUPERIOR`, `SUPERIOR`, `INICIAL`, `CAM` y `FORMACIÓN PARA EL TRABAJO` (verificado con
conteos reales). El segundo filtro, por `nivel` en básica, es el que de verdad acota al alcance
del proyecto (confirmado contra el fixture real de DS-01: solo trae PREESCOLAR/PRIMARIA/SECUNDARIA).

## 6. Llave de unión
- **CCT** (escuela) → **clave INEGI de 5 dígitos** para el nivel municipal.

## 7. Driver que alimenta
- Ninguno directamente: **es la llave de integración** y aporta la georreferencia usada por todos los
  cruces geográficos (interpolación IDW de D5/D6, asignación municipal de D1/D2).

## 8. Licencia de uso
- Términos de Libre Uso MX — **confirmar** en la ficha oficial.

## 9. Prueba de descarga real — **EJECUTADA**
- [x] Archivo descargado físicamente (las dos partes, vía SIGED, 29-ago-2026)
- [x] Abierto y con datos utilizables (encoding Latin-1 resuelto)
- [x] Registros contados: `597,685` filas crudas nacionales (332,888 + 264,797, sin encabezado)
  → `77,712` escuelas de educación básica en las 4 `SCOPE_ENTIDADES` (CDMX 13,495 · Jalisco
  21,532 · Edomex 32,423 · Nuevo León 10,262), tras aplicar `C_TIPO=="ESCUELA"` +
  `nivel ∈ {PREESCOLAR, PRIMARIA, SECUNDARIA}`
- [x] Esquema verificado (columnas y tipos, ver §5 — 92 columnas reales, mapeo documentado)
- [x] Llave confirmada: **0 CCT duplicados** en las 4 entidades tras el filtro de universo;
  georreferencia presente salvo 6 filas en 0,0 (ver riesgo abajo)
- **Responsable:** Diana Aracely Alvarez Varela · **Fecha:** 30-ago-2026
- **Extractor/cargador:** `src/ingesta/cargar_bronze_cct_real.py` (`bronze.cct_siged_202608`),
  pruebas en `tests/test_cargar_bronze_cct_real.py`. Detalle completo en el DevLog de esta sesión.

## 10. Riesgos conocidos
- CCT dados de baja o reactivados (planteles que cierran/abren) — no medible desde una sola
  descarga puntual, requiere comparar snapshots en el tiempo.
- **Coordenadas erróneas (0,0):** existían, 6 filas verificadas en las 4 `SCOPE_ENTIDADES`
  (fracción mínima de 77,712). **Corregido (BUG-034, 30-ago-2026):** `silver/escuela.sql`
  ahora nulifica también el 0 numérico, no solo la cadena vacía —
  `nullif(nullif(trim(cast(latitud as text)), '')::double precision, 0)` — con guarda de
  regresión en `dbt/tests/valid_escuela_georreferencia.sql`.
- Duplicados de CCT por turnos (matutino/vespertino): **no se materializó** — 0 duplicados
  verificados contra el archivo real filtrado a escuelas de básica.
- Homologación de claves de municipio (3 vs 5 dígitos): **confirmado real** — `INMUEBLE_CV_MUN`
  es el código local de 3 dígitos; `normalize_cve_mun(entidad, municipio)` en
  `silver/escuela.sql` ya sabe concatenar, no requiere cambios.

## 11. Calidad de datos (Great Expectations) — 2026-09-03

Suite nueva para Bronze (`bronze.cct_siged_202608`), cerrando la deuda señalada por Deni
Garrido en su auditoría del 30-ago (ver DevLog 2026-08-30-diana-alvarez-ds02-cct-real, sección
Pendiente).

- **Módulo:** `src/ingesta/validacion_cct.py` (`validar_cct()`), mismo patrón que
  `validacion_sesnsp.py` (TEST-011/US-124b): reutiliza `parsear_y_combinar()` de
  `cargar_bronze_cct_real.py` (no duplica esa lógica), o acepta un DataFrame explícito.
- **Expectativas:** not_null en columnas críticas, formato real de `cct` (`EE` + 3 letras +
  4 dígitos + 1 letra), `entidad`/`municipio` (2/3 dígitos), `nivel` restringido a
  PREESCOLAR/PRIMARIA/SECUNDARIA (el loader ya filtra a esto, si falla es regresión real del
  filtro), `cct` único dentro de una extracción (el loader ya truena si hay duplicado entre
  las dos partes). **No** excluye `latitud`/`longitud` en `0,0` — BUG-034 (6 filas reales
  conocidas) es un defecto de la fuente que corrige Silver, no Bronze; exigirlo aquí duplicaría
  esa responsabilidad y haría fallar la suite en datos reales conocidos. No se valida
  `sostenimiento` contra un catálogo — el loader lo pasa tal cual sin traducir, no se conoce su
  value_set real crudo con certeza.
- **Suite persistida:** `great_expectations/expectations/suite_ds02_cct.json`.
- **Pruebas offline (5):** `tests/test_validacion_cct.py` — datos limpios pasan (incluida la
  coordenada 0,0 conocida, que no debe romper la suite), y se verifica que SÍ atrapa nivel
  fuera de básica, cct duplicado y cct mal formado. Corren sin red ni CSV reales.
- **Pendiente:** correr `validar_cct()` contra los CSV reales (no solo el DataFrame sintético
  de las pruebas) para confirmar que el catálogo completo pasa limpio — no verificado en esta
  sesión por falta de acceso a los CSV reales (viven en el equipo de Diana) desde el entorno de
  IA.
