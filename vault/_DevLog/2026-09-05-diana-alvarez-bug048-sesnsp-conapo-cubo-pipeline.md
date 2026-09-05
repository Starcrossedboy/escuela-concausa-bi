---
project: "FARO"
date: "2026-09-05"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (Cowork)"
model: "claude-sonnet-5"
session_duration: "sesión larga, multi-etapa"
touches: ["DS-04", "DS-06", "DS-08", "BUG-048", "US-113", "US-122b", "REQ-001"]
tags: [devlog, ai-assisted, bug, sesnsp, conapo, conagua, cubo-pipeline, gold-dump, freeze]
---

# DevLog — 2026-09-05 — Diana Aracely Alvarez Varela — BUG-048: SESNSP real, CONAPO diagnosticado y cubo_pipeline destrabado para Deni

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva]] ·
[[vault/14_Data_Sources/DS-08_CONAPO_Proyecciones]] · [[vault/06_Quality_Testing/Bug_Register]]

## Qué se pidió

Verificar en serio, no por intuición, una sospecha propia: "estoy casi segura que el D2 es mío,
¿lo podemos comprobar?" — si el hueco de completitud del driver D2 (inseguridad) caía dentro del
alcance de Célula 1. De confirmarse, resolverlo primero y avisar después a Luis García (dueño de
DS-04), en vez de escalarlo sin evidencia.

## Qué se encontró — BUG-048 (DS-04/SESNSP)

Verificado contra el repo real y contra Postgres, no contra el reporte de nadie: el cargador real
`src/ingesta/cargar_bronze_sesnsp_real.py` ya existía (construido por Luis García un día antes),
pero `dbt/models/sources.yml` seguía apuntando el source `sesnsp` al identifier del fixture:

```
identifier: "{{ var('bronze_sesnsp_identifier', 'sesnsp_test') }}"
```

Es decir, cualquier ambiente que corriera `dbt run` sin pasar la var explícita seguía leyendo
`bronze.sesnsp_test` (fixture, ≤500 filas) en vez de `bronze.sesnsp` (real, 12,553,440 filas,
32 entidades, ya validado por Luis García el 24-ago con Great Expectations 14/15 — ver
`DS-04_SESNSP_Incidencia_Delictiva.md` §9). **Sí era alcance de Célula 1**: el archivo es de
dbt/models, dentro del alcance declarado de Diana en `ownership.yml`, y no tocaba nada de DS-06.

**Fix:** default corregido a `'sesnsp'`. `dbt run` sin `--vars` verificado contra Postgres real:
`silver.delitos_municipio` cruza **2,486 municipios** reales. `comp_media` de D2 se mantiene
estable (0.4861 / 0.4827 / 0.4804 por ciclo) — el fix no rompe nada existente, corrige la fuente
de fondo. Commit `165c911` en `dev/diana-alvarez`:
`fix(ds04): apunta bronze.sesnsp al identifier real, no al fixture (BUG-048)`. Avisado a Luis
García.

## Segundo hallazgo — DS-08/CONAPO sigue bloqueando D2 de fondo

El fix de arriba no movió la completitud de D2 en el cubo — señal de que el hueco real está en
otro lado de la misma cadena. Rastreado el CTE de D2 en `gold/fact_escuela_ciclo.sql`
(`poblacion_municipal` → `delitos_tasa` → `d2`): la tasa usa la población de
`{{ ref('poblacion_municipio') }}` (CONAPO) como denominador, y `bronze.conapo_sample` sigue
siendo el fixture (36 filas, 12 municipios) — `sources.yml` nunca se movió de
`bronze_conapo_identifier`/`'conapo_sample'`. Emilio Galnares (dueño de DS-08) no había
respondido a la fecha de este DevLog.

**Se investigó si Célula 1 podía re-obtener la población municipal real por su cuenta**, dado el
freeze de mañana:
- `datos.gob.mx` (URL de `extractor_conapo.py`) → 403 (Akamai, mismo bloqueo ya documentado para
  SESNSP antes del mirror ATDT).
- Mirror comunitario (`datamx.codeandomexico.org`) → certificado SSL expirado, descartado por no
  confiable.
- Mirror ATDT (`repodatos.atdt.gob.mx/CONAPO/...`) → es el producto de "Conciliación demográfica
  1950-2019 + Proyecciones 2020-2070", confirmado **solo a nivel estatal/nacional**, no
  municipal — grano equivocado, descartado.
- `github.com/lapanquecita/poblacion-estimada` → **candidato viable**, mismo autor que el mirror
  de respaldo ya documentado para SESNSP, licencia MIT, SSL válido, `total.csv` con población
  municipal (`CVE, Entidad, Municipio, 1990…2040`) suficiente para el denominador de D2. **No
  adoptado hoy** — queda documentado como opción, pendiente de decisión explícita si Emilio no
  responde antes del freeze, para no sustituir en silencio el pipeline que ya le pertenece a él.

Emilio fue contactado directamente pidiéndole la fuente real; sin respuesta al cierre de esta
sesión.

## Tercer hallazgo — `cubo_pipeline`/US-113 bloqueaba a Deni, sin depender de Emilio

Deni Garrido no podía correr su parte de US-113 (con su laptop además fuera de servicio) porque
`gold.cubo_pipeline` fallaba por falta de `bronze.conagua_presas` en el ambiente local — un hueco
de *datos*, no de código: el extractor y el cargador de DS-06/CONAGUA (`extractor_conagua.py`,
`cargar_bronze_conagua_real.py`) ya existían y funcionan, simplemente nadie los había vuelto a
correr en este ambiente. Corridos en vivo: 180 presas reales insertadas en
`bronze.conagua_presas`, `dbt run --select gold.cubo_pipeline` → 11 filas. Con esto,
`cubo_pipeline` ya no depende de nada pendiente de Emilio para D2/D5 en cuanto a estructura —
salvo, otra vez, DS-08.

**Hallazgo abierto, no comunicado todavía a Deni/Edgar:** `bronze.conapo_sample` (el fixture)
lleva `_source = 'DS-08_CONAPO'` — el mismo literal que usaría una extracción real — y el filtro
de `cubo_pipeline.sql` hace match exacto por ese string. Resultado: DS-08 se reporta
`cobertura_pipeline = 'OK'` con 36 filas (el conteo exacto del fixture) aunque no sea dato real.
Esto valida en concreto la preocupación que Deni ya había planteado sobre ambigüedad
fixture/dato-real — queda para discutirlo con ella y con Edgar, no se corrigió hoy (toca el
contrato de `_source` que usan varios modelos, no solo éste).

## Entrega a Célula 3 y Célula 5 (sin esperar a Emilio)

Para no bloquear más al equipo de cara al freeze de mañana, se regeneraron y entregaron dos dumps
de Gold (patrón reversible: cubo → tabla → `pg_dump` → cubo de vuelta a vista materializada),
ambos verificados con evidencia real (conteo de `COPY`/`DROP TABLE IF EXISTS` contra el número de
tablas esperado, filas cruzadas contra lo que ya había corrido en terminal):

- `gold_bug048_drivers_2026-09-05.sql` (10 tablas base + 8 cubos originales) → mismo archivo dado
  a Luis Téllez (C5), entregado también a Andrés González Habib (C3) para no generar versiones
  distintas entre ambos; con instrucciones de carga vía `psql` y aviso de que si su ambiente ya
  corrió `dbt run`, los cubos existen como vista materializada y hay que tirarlos antes de
  restaurar (el dump no trae `CREATE SCHEMA` ni maneja ese choque de tipo de objeto).
- `gold_bug048_pipeline_2026-09-05.sql` (igual + `cubo_pipeline`, 19 tablas) → entregado a Deni
  Garrido para que valide US-113 de punta a punta ahora mismo, con el caveat explícito de que
  todo es real salvo DS-08/CONAPO (sigue fixture) y que tendrá que recargar esa pieza en cuanto
  Emilio responda.

## Decisiones tomadas (no delegadas a la IA)

1. Confirmar con evidencia real (no con la intuición) que D2/SESNSP era alcance de C1 antes de
   tocar nada — commit y aviso a Luis García solo después de verificar.
2. No esperar a Emilio para destrabar a Deni — entregar el dump actual con el hueco de DS-08
   explícito, en vez de dejarla bloqueada por una fuente que no depende de ella.
3. Darle a Andrés el mismo dump que a Luis Téllez, no uno más nuevo, para mantener una sola
   versión de referencia entre C3 y C5.
4. No adoptar el mirror alterno de GitHub para CONAPO sin decisión explícita — queda documentado,
   no implementado, mientras siga habiendo posibilidad de que Emilio responda antes del freeze.
5. No corregir hoy el contrato de `_source` que permite que el fixture de DS-08 se lea como "OK"
   en `cubo_pipeline` — es un cambio de contrato compartido, se documenta como hallazgo abierto en
   vez de parcharlo sin avisar a quien más lo consume.

## Archivos modificados

- `dbt/models/sources.yml` — fix BUG-048 (commit `165c911`).
- `vault/06_Quality_Testing/Bug_Register.md` — alta de BUG-048.
- `vault/02_Requirements/Traceability_Matrix.md` — fila `REQ-001` de hoy.
- `vault/_DevLog/_index.md` — nueva fila.
- `vault/_DevLog/2026-09-05-diana-alvarez-bug048-sesnsp-conapo-cubo-pipeline.md` (este archivo).
- Dumps de Gold (`gold_bug048_drivers_2026-09-05.sql`, `gold_bug048_pipeline_2026-09-05.sql`) —
  **fuera de git** por diseño (CLAUDE.md, "nunca subas datos reales pesados"), compartidos por
  Teams. **Pendiente de acción:** ambos, y otros `.sql`/`.patch` sueltos en la raíz del repo de
  esta misma sesión, no están todavía en `.gitignore` (solo `*.dump` lo está) — riesgo real de
  subirlos por accidente con un `git add -A`. Ver sección de bloqueantes.

## Seguridad / calidad

- [x] Sin secretos hardcodeados
- [ ] **Hallazgo de hoy, no resuelto:** dumps `gold_bug048*.sql` y `gold_cubos_l2_2026-09-05.sql`
  en la raíz del repo NO están gitignorados (`git check-ignore` confirma "NO IGNORADO" en los 6
  archivos + `US106_freeze_para_edgar.patch`). Recomendado: extender `.gitignore` (línea 87,
  junto a `*.dump`) o moverlos fuera del repo, mismo criterio ya usado el 3-sep para
  `bronze_real_2026-09-03.dump`.
- [x] `dbt run`/`dbt test` verificados contra Postgres real, no contra fixture
- [x] DevLog enlaza a los IDs afectados

## Bloqueantes

- Emilio Galnares Ruiz no ha respondido con el extractor real de DS-08/CONAPO — bloquea el cierre
  completo de D2 (y de D1, que también usa población CONAPO). Escalado directamente a él.
- Riesgo de datos reales sin gitignorar en la raíz del repo (ver arriba) — no bloquea el freeze
  pero sí es una acción pendiente antes del PR.

## Próximos pasos

- Si Emilio no responde antes del freeze: decisión explícita de Diana sobre adoptar
  `lapanquecita/poblacion-estimada` como fuente alterna de DS-08, mismo criterio ya usado para
  SESNSP (verificar en vivo antes de programar, documentar como fuente alterna, no reemplazo
  silencioso).
- Compartir con Deni y Edgar el hallazgo de `cubo_pipeline` reportando DS-08 como falso "OK".
- Gitignorar o mover fuera del repo los dumps sueltos de esta sesión.
