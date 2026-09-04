---
project: "FARO"
date: "2026-09-03"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (Cowork)"
model: "claude-sonnet-5"
session_duration: "sesión larga, multi-etapa"
touches: ["DS-01", "DS-02", "REQ-001", "BLOCK-004"]
tags: [devlog, bronze, ds01, ds02, carga-real, dbt, gold, bloqueo-equipo, great-expectations]
---

# DevLog — 2026-09-03 — Diana Aracely Alvarez Varela — Carga real histórica DS-01, fix de contaminación en Gold y bloqueo de ambiente (BLOCK-004)

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/14_Data_Sources/DS-01_Formato_911]] ·
[[vault/10_Risk_Governance/Blocker_Register]] ·
[[vault/_DevLog/2026-09-03-diana-alvarez-cierre-ds01-ds02|DevLog de cierre, mismo día]]

## Qué se pidió

Tras el cierre formal de DS-01/DS-02 (ver DevLog enlazado arriba), verificar en serio dos puntos
que habían quedado como "Pendiente (no bloqueante)": el conteo real de ciclos contra Postgres, y
la deuda de Great Expectations — y, de ser afirmativo que seguían pendientes, resolverlos.

## Qué se encontró

- **`bronze.formato911_historico` era fixture, no carga real.** Verificado en vivo contra
  Postgres: 30-32 filas por ciclo en los 6 ciclos (tamaño del fixture de BUG-026), no las
  ~230 mil que documenta DS-01 §9 para cada ciclo. Esta tabla es la que alimenta el target real
  de `target_hibrido.py` (PR #56, Héctor Morales) vía `gold.matricula_municipio_nivel` — no es
  la misma tabla que cargó PR #105 (`bronze.formato911_2024_2025`, ciclo único, esa sí real).
- **Carga real ejecutada.** Nuevo script `src/ingesta/cargar_bronze_formato911_historico_real.py`
  (hoy commiteado — antes vivía solo local, sin commitear). Aditivo puro, sin DELETE/UPDATE/DROP
  (CLAUDE.md): ~1.37 millones de filas nuevas insertadas a través de los 6 ciclos
  (2019-2020→2024-2025), confirmado que las filas del fixture anterior siguieron intactas.
- **Dos casos de materialización obsoleta de dbt, no bugs de código.** `ref('escuela')` seguía
  sirviendo 72 filas (una tabla materializada desde el 19-ago, un fixture/seed) hasta correr
  `dbt run --select escuela+`; el mismo patrón se repitió con `silver.matricula_historica` hasta
  correr `dbt run --select matricula_historica+`. Lección para el equipo: dbt materializa tablas
  físicas, no vistas vivas — un `ref()` no se recalcula solo, hay que correr el DAG explícito tras
  cargar Bronze nuevo.
- **Contaminación real cuantificada y corregida en Gold.** De 182 filas fixture viejas que
  conviven con la carga real en `bronze.formato911_historico` (append-only, nunca se borran), 146
  caen dentro de `SCOPE_ENTIDADES` tras normalizar, y de esas solo **6** tienen un `cct` que
  coincide con el catálogo real de DS-02. Fix en `dbt/models/gold/matricula_municipio_nivel.sql`:
  `inner join` contra `silver.escuela` (catálogo real) antes de sumar, mismo principio que el
  filtro de `scope_entidades()` que ya existía. Verificado: `dbt test --select
  matricula_municipio_nivel` → 6/6 en verde, incluido
  `unique_matricula_municipio_nivel_cve_mun_nivel_ciclo`.

## `dbt run` + `dbt test` completo (red de seguridad, a petición de Diana)

- **2 modelos rotos por trabajo de otros compañeros recién mergeado a `main`** —
  `silver.agua_region` y `silver.rezago_municipio` fallan por `relation does not exist`
  (`bronze.conagua_no_ingerido` / `bronze.coneval_irs_2020` no están en este Postgres local).
  **No es deuda de Célula 1** — pendiente identificar los PRs exactos (no confirmados por número
  en esta sesión) y avisar a sus dueños (DS-06/DS-07).
- **3 fallas propias, genuinas, sin resolver todavía:** `unique_matricula_historica_cct_ciclo`
  (3) y `accepted_values_matricula_historica_nivel` (1). Causa raíz diagnosticada: las 6 filas
  fixture con `cct` real (ver arriba) sobreviven el dedup por turno de
  `silver/matricula_historica.sql` (`partition by cct, ciclo, turno`) porque su `turno` no
  coincide con el de la carga real para el mismo `cct+ciclo` — sobreviven como filas duplicadas a
  grano `(cct, ciclo)`. El filtro de catálogo real que ya se aplicó en Gold **no alcanza a
  corregir esto**, porque el `cct` de esas 6 filas sí existe en el catálogo real. Fix propuesto
  (no implementado hoy): un segundo dedup en Silver a grano `(cct, ciclo)`, quedándose con
  `_ingested_at` más reciente. **Queda como deuda explícita, no como "ya resuelto".**

  **Corrección (mismo día, más tarde):** esta hipótesis de causa raíz resultó **incorrecta** —
  ver "Actualización — dedup fix" más abajo para el diagnóstico real (verificado con datos
  reales) y el fix efectivamente aplicado.
- `not_null_dim_escuela_sostenimiento` (6) — no investigado a fondo hoy, posiblemente
  preexistente.

## Bloqueo de ambiente — BLOCK-004 (nuevo, alta hoy)

Edgar reportó que, salvo Diana, nadie del equipo tiene un ambiente local con Bronze real
cargado — bloquea `gold.cubo_pipeline` (DB-10, Oscar) y la validación con datos reales de
US-222/US-223 (PR #192, Oscar) y US-224. Registrado en
[[vault/10_Risk_Governance/Blocker_Register|Blocker_Register.md]] como **BLOCK-004**
(`mitigating`, dueña Diana). Documentados dos caminos en
[[vault/14_Data_Sources/DS-01_Formato_911|DS-01_Formato_911.md]] §11:

- **Camino A** (reproducir la carga real): ya disponible para cualquiera hoy mismo, ahora que el
  script histórico está commiteado — no dependía de nada más.
- **Camino B** (restaurar un `pg_dump` del schema `bronze` de Diana, minutos en vez de horas):
  **dump ya generado** por Diana (`bronze_real_2026-09-03.dump`, 33 MB, corrido en su propia
  terminal — esta sesión de IA no tiene acceso de red a su Postgres local), movido fuera del
  repo (`~/Documents/MTIIA/bronze_dumps/`) y `*.dump` agregado a `.gitignore` como candado extra.
  Pendiente solo de que Diana lo suba al canal de Teams del equipo y comparta el link.

**Nota de precisión:** el bloqueo queda `mitigating`, no `resolved` — con el dump ya generado,
lo único que falta para que sea `resolved` del todo es que Diana lo comparta por Teams (fuera
del alcance de esta sesión de IA: no hay forma de subir archivos a Teams desde aquí).

### Actualización — Camino A automatizado (mismo día, más tarde)

A petición de Diana ("queda más automatizado"), se automatizó también Camino A, no solo
documentado. `src/ingesta/extractor_cct.py` descarga DS-02 en automático llamando a la API real
que usa el propio portal SIGED — descubierta inspeccionando en vivo el JS del portal
(`tablas_siged.js`) y su llamada de red real, nunca inventando una URL (CLAUDE.md). Dos
problemas reales encontrados y resueltos en el camino, ambos verificados con Diana corriendo el
pipeline en su terminal real:

- **SSL:** `SSLCertVerificationError` al llamar `api.siged.sep.gob.mx` desde Python — `curl -sv`
  confirmó que el certificado es válido (usa el llavero del SO), así que era el bundle propio de
  `certifi` el que fallaba, no el servidor. Fix: `truststore.inject_into_ssl()` (agregado a
  `requirements/celula-1.txt`), que hace que Python use el mismo almacén de confianza del SO que
  ya usa `curl` — no es bajar la verificación.
- **Conexión cortada (`RemoteDisconnected`):** la API tolera una llamada pero cortaba la conexión
  sin responder en la segunda llamada seguida (probable límite de tasa/anti-bot). Fix: sesión
  compartida con cabeceras de navegador (User-Agent/Referer/Origin) + reintento con backoff +
  pausa de 2s entre las 2 partes del catálogo.

`src/ingesta/reproducir_bronze_real.py` (nuevo) orquesta DS-02 automático + DS-01 histórico en un
solo comando. Corrida real de Diana, limpia de punta a punta: 385,204 filas en
`bronze.cct_siged_202608`, ~1.37M filas nuevas en `bronze.formato911_historico` (6 ciclos). No
incluye `bronze.formato911_2024_2025` (PR #105, portal distinto, sin automatizar todavía).

`vault/14_Data_Sources/DS-01_Formato_911.md` §11 y `Blocker_Register.md` (BLOCK-004) actualizados
para reflejar que Camino A ya es un comando único, no un runbook manual.

## Qué se corrigió/agregó en el vault y el código

- `dbt/models/gold/matricula_municipio_nivel.sql` — fix de contaminación (ver arriba).
- `src/ingesta/cargar_bronze_formato911_historico_real.py` — nuevo, commiteado.
- `vault/14_Data_Sources/DS-01_Formato_911.md` — nueva §11 (runbook Camino A/B).
- `vault/10_Risk_Governance/Blocker_Register.md` — alta de BLOCK-004.
- `vault/_DevLog/2026-09-03-diana-alvarez-cierre-ds01-ds02.md` — sección Pendiente actualizada
  (el punto de "confirmar ciclos contra Postgres" ya no aplica tal cual: se confirmó que **no**
  estaba cargado y se cargó real hoy).

## Actualización — dedup fix + Great Expectations (mismo día, más tarde)

**Fix de dedup en `matricula_historica.sql` — dos intentos, el primero incorrecto.**

*Primer intento (fallido, confirmado por Diana):* CTE `lote_mas_reciente`, basada en la hipótesis
de que filas fixture viejas con `cct` real chocaban contra la carga real por `_ingested_at`.
Diana corrió `dbt run --select matricula_historica+ && dbt test --select matricula_historica`
contra su Postgres real y el resultado fue **idéntico** al de antes del fix (mismos 3+1 tests en
rojo) — la hipótesis quedó descartada por datos reales, no se volvió a adivinar un segundo fix.

*Diagnóstico real* (`dbt show --inline` contra Postgres, con Diana): el `cct` que rompe los 3
tests de unicidad es `11PDI0085S`, en los 3 ciclos que fallaban (2019-2020, 2023-2024,
2024-2025) — el patrón se repite idéntico en los 3, incluido el ciclo que solo tiene carga real,
lo que descarta un choque fixture-vs-real. Causa real: esa escuela reporta, en **todos** sus
ciclos, `turno=1` con `nivel=INICIAL` y `turno=2` con `nivel=PREESCOLAR` — un plantel con
educación inicial además de preescolar. `INICIAL` nunca estuvo en el alcance declarado del
modelo (`schema.yml`, `accepted_values` de `nivel`: solo `PREESCOLAR`/`PRIMARIA`/`SECUNDARIA`,
mismo criterio que `NIVELES_BASICA` en la suite de Great Expectations de este mismo día). Sin
filtrarlo, el turno `INICIAL` sobrevivía el dedup por turno y el `GROUP BY` final partía la
escuela en dos filas para el mismo `(cct, ciclo)`.

*Fix real, aplicado:* nueva CTE `nivel_basica`, que filtra a
`nivel in ('PREESCOLAR', 'PRIMARIA', 'SECUNDARIA')` — el alcance que el propio modelo ya
declaraba — antes del dedup por turno. Se retiró la CTE `lote_mas_reciente` (basada en la
hipótesis incorrecta). **Verificado contra Postgres real por Diana:**
`dbt run --select matricula_historica+ && dbt test --select matricula_historica` →
`PASS=8 WARN=0 ERROR=0` (los 8 tests del modelo, incluidos los 3+1 que fallaban, en verde).

**Great Expectations para DS-01 (histórico) y DS-02.** Cierra la deuda señalada por Deni Garrido
el 30-ago. Dos módulos nuevos, mismo patrón que `validacion_sesnsp.py` (TEST-011/US-124b):
`src/ingesta/validacion_cct.py` (DS-02, reutiliza `parsear_y_combinar()`) y
`src/ingesta/validacion_formato911_historico.py` (DS-01 histórico, lee el Parquet más reciente).
Detalle de las expectativas y por qué se excluyó cada cosa que no se pudo verificar con certeza
(`sostenimiento` de DS-02, coordenadas 0,0 de BUG-034, unicidad de `cct+ciclo+turno` en Bronze
DS-01) en `DS-02_Catalogo_CCT.md` §11 y `DS-01_Formato_911.md` §12. **10 pruebas offline nuevas**
(`tests/test_validacion_cct.py`, `tests/test_validacion_formato911_historico.py`) corridas real
en esta sesión — las 10 pasan, incluyendo los casos que deben fallar a propósito (nivel fuera de
básica, cct duplicado/mal formado, matrícula negativa, ciclo mal formado, nulo en columna
crítica). Las suites (`suite_ds02_cct.json`, `suite_ds01_formato911_historico.json`) quedan
registradas en `great_expectations/expectations/`.

**Actualización — verificado contra los archivos reales completos (mismo día, más tarde).**
Con `data/bronze/formato911_historico/*.parquet` y `data/bronze/cct/*.csv` ya presentes en el
repo (de la corrida real de Camino A), se corrieron las dos suites contra los datos reales
completos, no la muestra sintética: DS-01 histórico, los 6 ciclos (2019-2020: 230,424 filas ·
2020-2021: 228,852 · 2021-2022: 228,804 · 2022-2023: 229,691 · 2023-2024: 231,534 · 2024-2025:
231,913), 13/13 expectativas en verde cada uno. DS-02, catálogo completo (los 2 CSV reales de
SIGED), 15/15 en verde. Sin hallazgos — el catálogo y las 6 cargas históricas pasan limpio.

## Pendiente (explícito, no resuelto en esta sesión)

- **Corrección:** `agua_region` no estaba "roto por PRs" — confirmado con DevLog de Deni
  (2026-08-30-deni-garrido-ds06-bronze-pipeline.md) y el propio DevLog de Diana de US-105
  (2026-08-19): D5 sigue `SIN_DATO` explícito porque CONAGUA no entrega el contrato
  diario/georreferenciado que pide `silver.agua_region` — es un hueco de fuente real y ya
  documentado, no una regresión de código. Sigue pendiente confirmar el estado real de
  `rezago_municipio` (DS-07) — no verificado en esta sesión.
- **2026-09-03, resuelto:** Diana compartió el dump de Bronze (Camino B de BLOCK-004) por
  Teams, canal general del equipo — ver `Blocker_Register.md`, BLOCK-004 ahora `resolved`.

## IDs tocados

`DS-01` · `DS-02` · `REQ-001` · `BLOCK-004`
