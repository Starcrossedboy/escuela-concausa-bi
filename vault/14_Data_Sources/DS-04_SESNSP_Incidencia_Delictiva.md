---
id: DS-04
title: "DS-04 · SESNSP Incidencia Delictiva"
owner: "Luis Enrique García Vázquez"
status: draft
traces_up: ["vault/01_Product/PRD", "vault/12_Roadmap_Sprints/PLAN_MAESTRO"]
tags: [data-source, bronze, driver-d2, ingesta-continua]
---

# DS-04 · SESNSP Incidencia Delictiva Municipal

> → [[vault/14_Data_Sources/_index]] · Prueba de descarga real **✅ COMPLETADA** (2026-08-24, vía fuente
> alterna — ver sección 2) · **Ingesta continua #1** (mensual).

## 1. Identificación
- **Nombre oficial:** Incidencia Delictiva del Fuero Común (nivel municipal).
- **Institución responsable:** SESNSP (Secretariado Ejecutivo del Sistema Nacional de Seguridad
  Pública).
- **Qué aporta al proyecto:** delitos y víctimas **por municipio**; base del entorno de inseguridad de
  la escuela.

## 2. Acceso
- **Portal oficial (landing):**
  `https://www.gob.mx/sesnsp/acciones-y-programas/datos-abiertos-de-incidencia-delictiva`
- **Enlace oficial bloqueado (referencia histórica):** archivo
  `Municipal-Delitos-2015-2025_jun2026.zip`, publicado como enlace de OneDrive/SharePoint:
  `https://sspcgob-my.sharepoint.com/:u:/g/personal/cni_sspc_gob_mx/IQAnMGiScnoTTr4J2J9mUZthAat6lEdo7-1MCUpQU4n4EwQ?e=1NpS13`.
  Siempre redirige a `login.microsoftonline.com` (con o sin `&download=1`) — **no es descarga
  pública anónima**, pese a estar catalogado como "datos abiertos". Decisión de Diana Alvarez
  (Tech Lead, 2026-08-22, PR #31): no perseguir credenciales para este enlace, usar una fuente
  alterna equivalente.
- **✅ URL de descarga real usada por el extractor (verificada 2026-08-24):**
  `https://repodatos.atdt.gob.mx/api_update/sesnsp/incidencia_delictiva/IDM_NM_dic25.csv`
  — mismo host que ya usa `extractor_formato911.py` (DS-01): es la infraestructura real de datos
  abiertos detrás de `datos.gob.mx` (la API CKAN de `datos.gob.mx` sigue bloqueada con 403 de
  Akamai, pero el archivo estático que esa API referencia sí es público). `HTTP 200`, sin login,
  contenido verificado idéntico al de SESNSP (mismas columnas, mismos valores de muestra).
- **Mirror de respaldo (comunidad, no oficial):**
  `https://raw.githubusercontent.com/lapanquecita/incidencia-delictiva/main/data/municipal.zip`
  — por si `repodatos.atdt.gob.mx` cambia de URL. No es la fuente primaria del extractor.
- **⚠️ Bug del CDN (Akamai):** si el cliente ofrece `Accept-Encoding: gzip` (lo que `requests` de
  Python manda por default), el servidor responde con un gzip roto/truncado (`Content-Length: 20`
  para un archivo de 380 MB). El extractor fuerza `Accept-Encoding: identity` para recibir el CSV
  real sin comprimir.
- **Formato:** CSV, codificación **latin-1** (no UTF-8 — los acentos se corrompen si se lee mal).
  Formato ANCHO: un mes por columna (Enero…Diciembre), un registro por
  municipio × año × tipo de delito × subtipo × modalidad.
- **Tamaño real:** 378 737 393 bytes (~380 MB) sin comprimir, corte a diciembre 2025.

## 3. Frecuencia real de actualización
- **Mensual** (publicación aproximada el día 20 de cada mes). → satisface el requisito de ingesta
  continua.

## 4. Cobertura geográfica y temporal
- **Geográfica:** Nacional, desagregado municipal.
- **Temporal:** serie **desde 2015** (metodología vigente); confirmar en la prueba de descarga.

## 5. Esquema real (confirmado en prueba de descarga, 2026-08-24)

**Fuente cruda (ATDT, formato ancho):** `Año, Clave_Ent, Entidad, Cve. Municipio, Municipio,
Bien jurídico afectado, Tipo de delito, Subtipo de delito, Modalidad, Enero…Diciembre` (un mes
por columna). Grano: municipio × año × tipo de delito × **subtipo** × **modalidad**.

**Resuelto: es el archivo de "Delitos" (carpetas de investigación), NO de víctimas.** El nombre
del recurso bloqueado en SharePoint era literalmente `Municipal-Delitos-...zip`; la nota abierta
en `dbt/models/silver/schema.yml` ("origen físico pendiente de confirmar como víctimas o
carpetas") queda resuelta: `conteo` = **carpetas de investigación**, no víctimas.

**Bronze (lo que produce `extractor_sesnsp.py`)** — agregado a nivel municipio/año/mes/tipo de
delito, sumando subtipo y modalidad (ver sección 10, por qué no se deja al dedup de Silver):

| Columna | Tipo | Nota |
|---|---|---|
| `cve_ent` | str | Clave de entidad **cruda**, sin padding (ej. `"1"`, `"21"`) |
| `cve_mun` | str | Código municipal **local** de 3 dígitos, ya sin el prefijo de entidad (ej. `"001"`) — `dbt/macros/normalize_cve_mun.sql` reconstruye la clave INEGI de 5 dígitos a partir de `cve_ent`+`cve_mun` |
| `anio` | int | 2015–2025 |
| `mes` | int | 1–12 |
| `tipo_delito` | str | Texto libre (Homicidio, Lesiones, Feminicidio, Extorsión, …) |
| `conteo` | int | Carpetas de investigación, sumadas sobre subtipo/modalidad |

## 6. Llave de unión
- **Clave INEGI de 5 dígitos** (municipio). Se cruza con la escuela vía su municipio (DS-01/DS-02).

## 7. Driver que alimenta
- **D2 · Inseguridad del entorno.**

## 8. Licencia de uso
- Términos de Libre Uso MX — **confirmar** en la ficha oficial.

## 9. Prueba de descarga real — **✅ COMPLETADA** (2026-08-24, vía fuente alterna)
- [x] URL real localizada y verificada (enlace oficial de SharePoint, bloqueado)
- [x] Fuente alterna localizada y verificada (`repodatos.atdt.gob.mx`, sección 2)
- [x] Archivo descargado físicamente — 378 737 393 bytes (~380 MB), 4 596 480 filas crudas
- [x] Abierto y con datos utilizables — agregado a Bronze por `extractor_sesnsp.py`
- [x] Registros contados: **12 553 440 filas** en Bronze (grano municipio/año/mes/tipo_delito,
  32 entidades, 2015–2025, 40 categorías de `tipo_delito`)
- [x] Esquema verificado (columnas y tipos) — ver sección 5
- [x] Llave confirmada: `cve_ent` (crudo, 1-2 dígitos) + `cve_mun` (crudo, 3 dígitos local) →
  `dbt/macros/normalize_cve_mun.sql` arma la clave INEGI de 5 dígitos
- [x] Validado con Great Expectations (`TEST-011`): **14/15 expectativas en verde** — la única
  falla es real y esperada: 1 fila de 12 553 440 con `conteo = -1` (CDMX, municipio local `006`,
  sep-2017, "Otros delitos que atentan contra la libertad personal"), casi seguro una corrección
  retroactiva de SESNSP (consistente con el riesgo ya documentado de que el archivo mensual
  reescribe históricos). No se "arregló" el dato — Great Expectations lo deja visible.
- **Responsable:** Luis Enrique García Vázquez · **Fecha:** 2026-08-24 (primer intento
  2026-08-14, bloqueado; destrabado 2026-08-22 por decisión de Diana Alvarez de usar fuente
  alterna en vez de perseguir credenciales de SharePoint)

## 10. Riesgos conocidos
- **Nuevo (2026-08-24, confirmado con Great Expectations — ver `TEST-011`):** 1 de 12 553 440
  filas trae `conteo = -1` (CDMX, municipio local `006`, sep-2017, "Otros delitos que atentan
  contra la libertad personal"). Consistente con que SESNSP reescribe históricos con
  correcciones — un mes puede llevar un ajuste negativo sobre un conteo previamente
  sobreestimado. No se corrigió en Bronze; queda como hallazgo visible en Data Docs.
- **Resuelto (2026-08-24):** el enlace oficial de SharePoint sigue exigiendo login Microsoft, pero
  ya no bloquea el proyecto — el extractor usa el mirror ATDT (ver sección 2), decisión de Diana
  Alvarez del 2026-08-22.
- **Nuevo (2026-08-24):** el CDN (Akamai) de `repodatos.atdt.gob.mx` devuelve un gzip roto/truncado
  si el cliente ofrece `Accept-Encoding: gzip` (default de `requests`). El extractor fuerza
  `identity`. Si algún día deja de funcionar, revisar primero este detalle antes de asumir que la
  fuente desapareció.
- **Nuevo (2026-08-24):** el CSV fuente es **latin-1**, no UTF-8 — leerlo sin especificar
  encoding corrompe los acentos (`Año` → `A�o`). `pandas.read_csv` además ignora el parámetro
  `encoding=` cuando se le pasa un stream binario crudo; hay que envolverlo en
  `io.TextIOWrapper(..., encoding="latin-1")` primero.
- **Nuevo (2026-08-24):** el grano nativo de la fuente es más fino que el que espera Silver
  (incluye subtipo y modalidad, no solo tipo de delito). El dedup de
  `delitos_municipio.sql` (`row_number()... keep _row_number=1`) **no suma** filas — si Bronze
  llegara al grano fino, se perdería conteo en vez de sumarlo. El extractor agrega
  (unpivot + `sum`) antes de escribir Bronze para evitar esto.
- **Resuelto (2026-08-24):** la nota abierta de `dbt/models/silver/schema.yml` sobre si `conteo`
  es víctimas o carpetas queda resuelta — es **carpetas de investigación** (el archivo se llama
  "Delitos", no "Víctimas").
- Cambios de metodología/clasificación de delitos entre años.
- Subregistro (cifra negra): no todos los delitos se denuncian.
- Municipios con cero reportado que en realidad es falta de dato → aplicar criterio `SIN_DATO`.
- El archivo mensual puede reescribir históricos (revisiones).
