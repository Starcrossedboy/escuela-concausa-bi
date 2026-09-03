---
project: "FARO"
date: "2026-09-03"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (Cowork)"
model: "claude-sonnet-5"
session_duration: "sesión larga, multi-etapa"
touches: ["DS-01", "REQ-001", "BLOCK-004"]
tags: [devlog, bronze, ds01, carga-real, dbt, gold, bloqueo-equipo]
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

## Qué se corrigió/agregó en el vault y el código

- `dbt/models/gold/matricula_municipio_nivel.sql` — fix de contaminación (ver arriba).
- `src/ingesta/cargar_bronze_formato911_historico_real.py` — nuevo, commiteado.
- `vault/14_Data_Sources/DS-01_Formato_911.md` — nueva §11 (runbook Camino A/B).
- `vault/10_Risk_Governance/Blocker_Register.md` — alta de BLOCK-004.
- `vault/_DevLog/2026-09-03-diana-alvarez-cierre-ds01-ds02.md` — sección Pendiente actualizada
  (el punto de "confirmar ciclos contra Postgres" ya no aplica tal cual: se confirmó que **no**
  estaba cargado y se cargó real hoy).

## Pendiente (explícito, no resuelto en esta sesión)

- Fix de dedup en `matricula_historica.sql` (grano `cct, ciclo`) — 3+1 tests fallando,
  diagnosticado, no implementado.
- Confirmar los 2 PRs exactos que rompieron `agua_region`/`rezago_municipio` y avisar a sus
  dueños.
- Great Expectations para DS-01/DS-02 — deuda conocida, sigue fuera de alcance de esta sesión.
- Compartir el dump de Bronze ya generado (Camino B de BLOCK-004) por Teams — acción de
  Diana, fuera del alcance de esta sesión de IA (no hay forma de subir archivos a Teams desde
  aquí).
- Responder a Oscar (DB-10/DB-07) y a Estefany (BUG-026/US-321) — comunicación de equipo, no
  técnica.

## IDs tocados

`DS-01` · `REQ-001` · `BLOCK-004`
