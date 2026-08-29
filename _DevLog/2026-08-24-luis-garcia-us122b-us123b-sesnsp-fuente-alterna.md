---
id: DEVLOG-2026-08-24-LUIS-US122B-US123B
title: "DevLog — DS-04 destrabada: fuente alterna, extractor real y Great Expectations"
author: "Luis Enrique García Vázquez"
session_date: "2026-08-24"
ai_tool: "Claude Code (Sonnet 5)"
traces_up: ["US-122b", "US-123b", "REQ-001"]
affected_ids: ["US-122b", "US-123b", "TEST-011", "REQ-001", "DS-04"]
tags: [devlog, ai-assisted, sprint-4, sesnsp, bronze, great-expectations, data-quality]
---

# DevLog — DS-04 destrabada: cierra US-122b y US-123b por completo

## Contexto

Diana había dado un plazo de "un par de días" (comentario del 2026-08-22 en el PR #31) para
encontrar una fuente pública alterna de incidencia delictiva municipal antes de dar el bloqueo de
DS-04 por definitivo. Esta sesión fue esa búsqueda, y terminó destrabando por completo `US-122b`
y `US-123b` para DS-04.

## Qué se pidió a la IA

> "usquemos si existe alguna fuente pública equivalente para la incidencia delictiva municipal de
> DS-04." → luego, tras confirmar el hallazgo: "Todo: doc + extractor + avisar a Diana."

## Qué hizo la IA (y qué se revisó)

### Búsqueda de fuente alterna

Delegó la búsqueda a un sub-agente con instrucciones de **no inventar URLs** y verificar cada
candidato con una petición HTTP real antes de reportarlo como viable. Encontró
`https://repodatos.atdt.gob.mx/api_update/sesnsp/incidencia_delictiva/IDM_NM_dic25.csv` — el
mismo host que ya usa `extractor_formato911.py` (DS-01) para su descarga.

**Revisión mía (con la IA, pero verificado por mí antes de confiar en el hallazgo):** no acepté el
reporte del sub-agente a ciegas — pedí confirmar con `curl` real: headers (`HTTP 200`,
`Content-Type: text/csv`, 378 737 393 bytes) y una muestra de contenido (columnas y valores) en
dos puntos distintos del archivo (entidad de 1 dígito y de 2 dígitos) para validar la hipótesis de
formato de `Cve. Municipio` antes de programar nada.

### Extractor real (`src/ingesta/extractor_sesnsp.py`)

Reemplazó el placeholder de Diana (que literalmente lanzaba un error señalando "dueño: Luis
García") por una implementación real. Encontró y resolvió **tres problemas reales, no obvios,**
solo detectables corriendo contra el archivo de verdad:

1. **Grano fino vs. grano esperado por Silver.** La fuente trae subtipo y modalidad de delito; el
   modelo `delitos_municipio.sql` espera (municipio, año, mes, tipo_delito) y hace *dedup* por
   `_ingested_at` (no suma). Si Bronze llegara al grano fino, ese dedup **perdería conteo** en vez
   de sumarlo. El extractor agrega (unpivot ancho→largo + `sum`) antes de escribir Bronze.
2. **Bug de CDN (Akamai).** Si el cliente ofrece `Accept-Encoding: gzip` (lo que `requests` manda
   por default), el servidor responde con un gzip roto (`Content-Length: 20` para un archivo de
   380 MB). Se fuerza `Accept-Encoding: identity`.
3. **Corte de conexión a media descarga.** El primer intento de leer el CSV en streaming directo
   sobre el socket HTTP (`pd.read_csv(response.raw, chunksize=...)`) se cortó dos veces distinto
   (`UnicodeDecodeError` por el gzip roto primero, luego `ValueError: I/O operation on closed
   file` a la mitad de la descarga tras arreglar el gzip). Se cambió a descargar completo a un
   archivo temporal primero y parsear desde disco después — más robusto para un archivo de este
   tamaño sobre una conexión no garantizada.

**Revisión mía:** verifiqué la lógica de agregación contra una muestra real antes de correr la
extracción completa (378 MB tardan varios minutos): confirmé que sumar las 4 modalidades de
"Homicidio doloso" da el mismo total que el dato original sin agregar, y confirmé a mano la
derivación de `cve_mun` (`"21002"` con `cve_ent="21"` → local `"002"`) contra dos entidades de
distinta longitud antes de aceptar la fórmula.

### Great Expectations para DS-04 (`src/ingesta/validacion_sesnsp.py`, `TEST-011`)

Mismo patrón de diseño que `TEST-010` (DS-05). El catálogo de `tipo_delito` se construyó **a
partir del corte real** (40 categorías confirmadas), no de una lista inventada.

## Resultado real (12 553 440 filas de Bronze, no una muestra)

- **14/15 expectativas en verde.**
- **1 hallazgo real:** `conteo = -1` en CDMX, municipio local `006`, sep-2017, "Otros delitos que
  atentan contra la libertad personal" — casi seguro una corrección retroactiva de SESNSP
  (consistente con el riesgo ya documentado de que el archivo mensual reescribe históricos). No lo
  "arreglé": Great Expectations lo deja visible en Data Docs, tal como se decidió con el hallazgo
  de georreferencia de DS-05 la semana pasada.

## Decisiones tomadas (no delegadas a la IA)

1. **No confiar en el reporte del sub-agente sin verificación propia** — exigí `curl` real antes
   de programar una sola línea del extractor.
2. **Agregar en el extractor, no en Silver.** Pude haber cambiado `delitos_municipio.sql` para que
   sumara en vez de deduplicar, pero decidí resolverlo en Bronze: el contrato original de la ficha
   DS-04 (escrito antes de que yo empezara) ya asumía Bronze a nivel tipo_delito sin subtipo, así
   que agregar ahí respeta el diseño existente en vez de tocar el modelo de otra persona (Deni)
   sin avisarle.
3. **Descargar a temporal en vez de insistir en streaming puro** tras el segundo fallo — prioricé
   robustez sobre "elegancia" de no tocar disco.
4. **Dejar visible el conteo negativo, no filtrarlo.** Mismo criterio que con la georreferencia de
   DS-05: el objetivo de la suite es encontrar problemas reales, no maquillarlos.

## Archivos modificados

- `src/ingesta/extractor_sesnsp.py` — extractor real (reemplaza el placeholder de Diana).
- `src/ingesta/validacion_sesnsp.py` — suite Great Expectations (`TEST-011`, nuevo).
- `06_Quality_Testing/Automated/Great_Expectations_DS04_Sesnsp.md` — `TEST-011` (nuevo).
- `06_Quality_Testing/Automated/_index.md` — registro de `TEST-011`.
- `14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva.md` — fuente alterna, esquema real, prueba de
  descarga completada, riesgos nuevos.
- `12_Roadmap_Sprints/Sprints/1-luis-enrique-garcia-vazquez.md` — `US-122b`/`US-123b` a Terminado.
- `02_Requirements/Traceability_Matrix.md` — fila `REQ-001`.
- `_DevLog/2026-08-24-luis-garcia-us122b-us123b-sesnsp-fuente-alterna.md` (este archivo).
- `_DevLog/_index.md` — nueva fila.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [x] No se suben datos reales pesados (`data/bronze/`, `great_expectations/uncommitted/`
  gitignored; el Parquet de 380 MB de origen ni siquiera toca el repo)
- [x] `ruff check` limpio, `py_compile` limpio
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes

Ninguno — DS-04 queda completamente destrabada.

## Próximos pasos

- Avisar a Diana en el PR #31 que la fuente alterna ya está encontrada, verificada y en
  producción (extractor + suite corriendo contra datos reales).
- `US-124b` (fixtures ≤500 filas de DS-04 y DS-05) sigue pendiente, vence este domingo 30-ago.
- Conectar ambos extractores/suites a un DAG en vez de correrlos manualmente (pendiente de antes).
