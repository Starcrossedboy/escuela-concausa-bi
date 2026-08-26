---
project: "FARO"
date: "2026-08-22"
author_human: "Diana Aracely Alvarez Varela"
agent: "Claude (Cowork)"
model: "claude-sonnet-5"
session_duration: "extensa -- multiples turnos, cruzo compactacion de contexto"
touches: ["RISK-007", "DEC-007", "BUG-009", "DS-01"]
tags: [devlog]
---

# DevLog — 2026-08-22 — Pipeline aislado de matrícula histórica (RISK-007/DEC-007): Bronze → Silver → Gold

→ [[_DevLog/_index|Volver al índice]]

## Qué se hizo
- Construido de punta a punta un pipeline **nuevo y aislado** para mitigar RISK-007/DEC-007
  (target híbrido de Héctor Morales, `src/modelos/target_hibrido.py`, PR #56): distribución
  HISTÓRICA multi-ciclo (2019-2020..2024-2025) de DS-01 Formato 911, sin tocar ni arriesgar
  `bronze.formato911`/`silver.matricula`/`gold.features_escuela` (ciclo único 2024-2025, ya
  en producción) ni el trabajo de nadie más del equipo.
- `src/ingesta/extractor_formato911_historico.py`: URLs de los 6 ciclos verificadas una por
  una a mano (no por fórmula — 2023-2024 y 2024-2025 rompen el patrón de años anteriores),
  detección explícita de la columna llave de escuela (`clave_cct` vs `clavecct`, sin adivinar
  un tercer nombre) y validación de columnas fijas antes de procesar. Validado contra los 3
  CSV reales descargados por Diana (230,424 / 228,804 / 231,913 filas, 0 `matricula_total` no
  numérico).
- `bronze.formato911_historico` (grano cct × ciclo × turno) → `silver.matricula_historica`
  (SUMA de `matricula_total` por turno — confirmado con datos reales que un mismo cct puede
  reportar más de un turno con matrícula distinta en el mismo ciclo) → `gold.matricula_municipio_nivel`
  (agregado municipio × nivel × ciclo, alias `ciclo`→`id_ciclo`, filtro SCOPE_ENTIDADES
  aplicado en el límite Silver→Gold). Este último entrega exactamente el contrato que exige
  `unir_target(..., validate="one_to_one")`: `dbt build` confirmó la unicidad real de
  `cve_mun × nivel × id_ciclo` (72/72 filas, test `unique_matricula_municipio_nivel_cve_mun_nivel_ciclo`
  en verde).
- Corregida una mala referencia propia (DEC-005 → DEC-007) en los comentarios del nuevo código,
  a partir de la colisión de IDs que Edgar ya había resuelto formalmente el 2026-08-19.
- **BUG-009 encontrado, investigado y registrado** (renumerado desde BUG-008 el 22-ago por
  Edgar — ver "Reconciliación BUG-008 → BUG-009" abajo): 7 de 10 fuentes Bronze en
  `sources.yml` sin `identifier` por default rompen cualquier `dbt build`/`dbt run` completo,
  aunque el modelo seleccionado no las use. Reportado a Edgar; a petición suya, registrado
  formalmente en `06_Quality_Testing/Bug_Register.md` (owner: Edgar).
- **Falsa alarma autocorregida (no llegó a registrarse como bug)**: se sospechó inicialmente
  que la sintaxis `accepted_values: → arguments: → values:` de Deni/Luis (Silver) estaba mal
  y causaba un error `'NoneType' object is not iterable`. Verificado con el código fuente
  real de dbt-core 1.12.0 (`require_generic_test_arguments_property: bool = True` por
  default) y con una corrida real de `dbt build` sin `--select`: esa sintaxis es la correcta
  y vigente, no un bug. Se revirtió el cambio que ya se había aplicado sobre
  `dbt/models/gold/_gold__models.yml` (archivo propio de Diana) para dejarlo consistente.
  Una corrida completa del proyecto confirmó 0 errores de ese tipo — cerrado con evidencia,
  nada que reportar a Deni/Luis.
- Detectado a media sesión que la rama de trabajo (`feat/diana-varela-us105-idw-aire`) era
  una rama de un feature distinto (US-105 IDW aire) ya mergeada hacía ~50 commits (PR #52).
  Movidos los cambios sin comitear a una rama nueva y limpia (`feat/diana-varela-matricula-historica-risk007`,
  basada en `origin/main` real) vía `git stash` + `checkout -b` + `stash pop`; un solo
  conflicto real (`Bug_Register.md`, por las filas de BUG-005/006/007 ya mergeadas que la
  rama vieja no tenía) resuelto sin tocar contenido de nadie.
- 12 pruebas unitarias nuevas para el extractor (`tests/test_extractor_formato911_historico.py`):
  detección de columna cct, validación de columnas fijas, coerción de `insc_t` no numérico,
  preservación de múltiples turnos por cct, y que no se intente descargar nada si algún ciclo
  pedido no tiene URL verificada. 12/12 en verde, corridas por el agente antes de entregarlas
  y confirmadas de nuevo por Diana en su máquina.

## Continuación 2026-08-22 (segunda sesión) — reconstrucción tras pérdida de estado

Al retomar la sesión (cruzando compactación de contexto), el contenedor apareció en un estado
inconsistente con lo documentado arriba:

- `HEAD` estaba **detached** en la punta de `feat/diana-varela-us103-gold-estrella` (un feature
  distinto, ya mergeado), no en `feat/diana-varela-matricula-historica-risk007`. Esa rama **no
  existía** — ni local ni en `origin` (verificado con `git ls-remote`) — y los "4 commits
  locales" que este mismo DevLog documentaba tampoco existían en ningún lado (ni en el historial,
  ni en objetos colgantes vía `git fsck`, ni en el stash). Todo el trabajo de RISK-007 estaba sin
  comitear, flotando en el working tree sobre la base equivocada.
- **Recuperado sin pérdida** vía `git stash push -u` → `git checkout -b
  feat/diana-varela-matricula-historica-risk007 origin/main` (que había avanzado, PR #66 incluido)
  → `git stash pop`. Conflictos reales (formato/indentación de merges ajenos ya en `main`, no
  contenido propio) en `_index.md` (ADRs), `_gold__models.yml`, `_gold__sources.yml` y
  `cargar_bronze_fixture.py` — resueltos sin tocar contenido de nadie más.
- **Confirmada pérdida real y acotada**: `dbt/models/gold/matricula_municipio_nivel.sql`, su test
  `unique_matricula_municipio_nivel_cve_mun_nivel_ciclo.sql`, las entradas correspondientes en
  `_gold__models.yml`/`_gold__sources.yml`, y el registro de BUG-009 (numerado BUG-008 en ese
  momento, ver "Reconciliación" abajo) en `Bug_Register.md` — todo descrito arriba como ya
  construido y validado (`dbt build`, 72/72 filas) — no sobrevivieron a la transición de
  contenedor. Sí sobrevivió un borrador en `/tmp/Bug_Register_final.md` (aplicado desde ahí). El resto (extractor, `silver.matricula_historica`, sus tests dbt, las 12
  pruebas unitarias, `sources.yml`/`schema.yml` de Silver) sí sobrevivió intacto.
- **Reconstruido, no recuperado**: con Diana confirmando seguir adelante, se reescribió
  `matricula_municipio_nivel.sql` (y su test + entradas YAML) desde cero siguiendo el spec ya
  documentado arriba (agregado `cve_mun × nivel × id_ciclo`, alias `ciclo`→`id_ciclo`, filtro
  SCOPE_ENTIDADES en el límite Silver→Gold, `source()` no `ref()`). Se dejó constancia en el
  propio archivo de que es una reconstrucción, no el original recuperado.
- **Vuelto a validar con datos y `dbt build` reales** (no solo `dbt compile`), desde cero en este
  contenedor: Postgres local levantado, `bronze.formato911_historico` recargado (182 filas, fixture
  de 3 ciclos), dependencia adaptador `dbt-postgres==1.11.0` reinstalada (faltaba en el entorno).
  `dbt build --select matricula_historica matricula_municipio_nivel` (en dos pasadas — el Gold usa
  `source()`, no `ref()`, así que no hay edge de dependencia automática entre ambos para una sola
  pasada con threads): `silver.matricula_historica` → **180 filas**, 6/6 tests PASS;
  `gold.matricula_municipio_nivel` → **72 filas** (igual que la corrida original), 5/5 tests PASS,
  incluido `unique_matricula_municipio_nivel_cve_mun_nivel_ciclo` en verde. `dbt build` completo
  del proyecto (sin `--select`): 103 PASS, 0 errores nuevos — los 4 errores restantes son de
  `agua_region`/`delitos_municipio`/`rezago_municipio`/`poblacion_municipio` (vars sin default
  ajenas, fuera de alcance de RISK-007, no tocadas). 12/12 pruebas unitarias del extractor
  re-confirmadas en verde. `vault_lint.py` corrido: vault limpio.
- Bug re-aplicado (numerado BUG-008 en ese momento, renumerado a BUG-009 el 22-ago, ver
  "Reconciliación" abajo) a `06_Quality_Testing/Bug_Register.md` (fila + detalle) desde el
  borrador recuperado de `/tmp`, cuidando no pisar las filas de BUG-005/006/007 que ya se
  actualizaron a `fixed` (PR #65, Luis Téllez) en `origin/main` desde la sesión original.

## Continuación 2026-08-22 (tercera sesión) — a petición de Edgar: SNIEE, 2º ciclo y vault

Edgar pidió (i) bajar la serie SNIEE municipio×nivel para las 4 entidades de `SCOPE_ENTIDADES`,
(ii) intentar en paralelo el 2º ciclo crudo del 911 (2023-2024) y (iii) dejar el vault al 100%.
Resultado, documentado con evidencia en `14_Data_Sources/DS-01_Formato_911.md` §9/§9a:

- **2º ciclo crudo (2023-2024): no se pudo intentar desde este entorno.** El contenedor cloud de
  esta sesión no tiene salida general a internet (`curl`/`bash` fallan hasta contra `google.com`),
  y `WebFetch` falló dos veces con `ROBOTS_DISALLOWED` contra `repodatos.atdt.gob.mx` (no logra
  obtener/parsear su `robots.txt`). La URL ya verificada por Diana
  (`.../f911/ESTANDAR_BASICA_I2324.csv`) no cambió — el bloqueo es del entorno, no del extractor
  ni de la URL. Queda pendiente intentarlo desde una máquina con salida a internet real.
- **Serie SNIEE municipio×nivel: no localizada, tras búsqueda razonablemente exhaustiva.** 7
  `WebFetch` + 4 `WebSearch` sobre los 3 portales que `DS-01_Formato_911.md` ya nombraba
  (planeacion.sep.gob.mx, siged.sep.gob.mx, snie.sep.gob.mx) más descubrimiento orgánico (Atlas de
  servicios educativos por estado, Principales Cifras, tabulados INEGI). Lo único público y
  descargable en bloque que existe es a nivel **entidad** (serie histórica 1990-91→2030-31); el
  Atlas por estado desagrega por municipio pero son indicadores de infraestructura/censo, no
  matrícula por nivel. No se encontró ningún sistema de consulta interactivo con URL pública
  enlazada. **Esto es un hallazgo que vale la pena escalar, no solo un "no encontrado todavía"**:
  la premisa de `DEC-007`/`DOC-TARGET-HIBRIDO` de que la serie SNIEE es "la misma fuente DS-01 en
  otra distribución" pública y descargable en bloque no quedó confirmada — ver el detalle y las
  alternativas propuestas en `DS-01_Formato_911.md` §9a.
- **Vault:** `vault_lint.py` ya reportaba `✅ Vault limpio` (huérfanos son solo informativos, no
  fallan el script). Se enlazó además este mismo DevLog desde `_DevLog/_index.md` (fila nueva),
  bajando los huérfanos de 4 a 3 — los 3 restantes son pre-existentes y ajenos a RISK-007, no se
  tocaron.

## 🤖 Sesión de IA
- **Agente / modelo:** Claude (Cowork), claude-sonnet-5
- **Archivos creados/modificados:**
  - `src/ingesta/extractor_formato911_historico.py` (nuevo)
  - `src/ingesta/cargar_bronze_fixture.py` (DDL/esquema de `bronze.formato911_historico`)
  - `tests/fixtures/generate_bronze_formato911_historico_fixtures.py` (nuevo)
  - `tests/fixtures/bronze_formato911_historico_sample.csv` (nuevo)
  - `tests/test_extractor_formato911_historico.py` (nuevo, 12 pruebas)
  - `dbt/models/sources.yml` (fuente `formato911_historico`)
  - `dbt/models/silver/matricula_historica.sql` (nuevo)
  - `dbt/models/silver/schema.yml` (tests de `matricula_historica`)
  - `dbt/tests/unique_matricula_historica_cct_ciclo.sql` (nuevo)
  - `dbt/models/gold/matricula_municipio_nivel.sql` (nuevo)
  - `dbt/models/gold/_gold__sources.yml` (fuente `matricula_historica`)
  - `dbt/models/gold/_gold__models.yml` (modelo + tests de `matricula_municipio_nivel`)
  - `dbt/tests/unique_matricula_municipio_nivel_cve_mun_nivel_ciclo.sql` (nuevo)
  - `06_Quality_Testing/Bug_Register.md` (registro de BUG-009, numerado BUG-008 en el momento
    de esta sesión)
- **Decisiones autónomas del agente:** conclusión inicial incorrecta sobre la causa raíz de un
  supuesto bug adicional (`accepted_values`/`arguments:` anidado — nunca llegó a registrarse
  con ID, no confundir con BUG-009 arriba), corregida en la misma sesión al contrastarla con
  evidencia real (código fuente de dbt-core + corrida real) antes de reportarla a nadie;
  usar `{{ source('silver', ...) }}` en vez de `{{ ref(...) }}` para el nuevo modelo Gold,
  verificado contra los modelos Gold reales existentes antes de escribir código nuevo; SUMAR
  por turno en Silver en vez de tomar el primero, verificado con datos reales de 2024-2025.
- **Correcciones manuales:** ninguna a nivel de código (todo se aplicó tal cual se entregó,
  verificado con `dbt build`/`pytest` reales antes y después de cada paso). A nivel de
  proceso, Diana detuvo el reporte a Deni/Luis del supuesto bug adicional (`arguments:`
  anidado) hasta confirmar con evidencia real que no había nada que reportar.
- **Prompt inicial:** continuación de sesión anterior (extractor ya validado contra datos
  reales; pendiente construir el pipeline completo Bronze→Silver→Gold).

## Seguridad / calidad
- [x] `python _Meta/scripts/vault_lint.py .` — vault limpio
- [x] Sin secretos hardcodeados
- [x] 12 pruebas unitarias nuevas (`tests/test_extractor_formato911_historico.py`), 12/12 en
      verde, corridas en dos máquinas distintas y re-confirmadas tras la reconstrucción
- [x] Validado con `dbt build` real (Bronze cargado, Silver y Gold corridos y probados con
      datos), no sólo `dbt compile` — dos veces: sesión original y tras la reconstrucción
- [x] DevLog enlaza a los IDs afectados (RISK-007, DEC-007, BUG-009)

## Bloqueantes
- ~~ID de historia formal pendiente~~ **resuelto 2026-08-22**: Diana decidió que esto no es una
  historia formal, es un arreglo/parte para avanzar — no lleva `US-###`. Nombre de rama genérico,
  sin ID: `feat/diana-varela-matricula-historica-risk007` (ya referencia RISK-007, que es lo que
  resuelve).
- ~~Respuesta de Edgar sobre BUG-008 (ya reportado y registrado) todavía pendiente~~
  **resuelto**: Edgar respondió renumerando el bug a **BUG-009** el 22-ago, por colisión con
  un BUG-008 distinto y preexistente (docker/api.Dockerfile) de otra rama — ver "Reconciliación
  BUG-008 → BUG-009" abajo.
- ~~Rama... no pusheada~~ **resuelto 2026-08-22**: Diana pusheó `feat/diana-varela-matricula-historica-risk007`
  desde su propia máquina, resolvió el conflicto de merge contra `origin/main` en
  `06_Quality_Testing/Bug_Register.md` (divergencia real: filas de BUG-005/006/007 ya actualizadas
  a `fixed` en PR #65, que la rama vieja no tenía) y volvió a pushear. `vault_lint.py` limpio y
  `pytest tests/ -q` en verde (221 passed, 4 skipped) confirmados después del merge.
- ~~2º ciclo crudo (2023-2024) del 911: no se pudo intentar... necesita reintentarse desde una
  máquina con salida a internet real~~ **resuelto 2026-08-22**: Diana ya tenía descargados y
  validó en su máquina los **6 ciclos completos** (2019-2020 a 2024-2025), no solo 3 — ver
  "Corrección 2026-08-22" abajo. El bloqueo de red solo aplicaba al entorno cloud de esta sesión,
  nunca a la máquina de Diana.
- **Serie SNIEE municipio×nivel**: no localizada tras búsqueda razonablemente exhaustiva (ver
  "Continuación" arriba y `DS-01_Formato_911.md` §9a) — **riesgo a escalar con Edgar/Célula 1**,
  la premisa de que es "DS-01 en otra distribución pública" no quedó confirmada. Gate del target
  real es el 30 de agosto (`DOC-TARGET-HIBRIDO`). Esta investigación quedó fuera del PR de
  RISK-007/DEC-007 (no era parte del alcance — malentendido de la sesión, corregido).

## Corrección 2026-08-22 — 6 ciclos, no 3

Un registro anterior de esta sesión subestimó el trabajo real: decía "3 ciclos reales
descargados" cuando Diana ya había descargado y comprobado los **6** (2019-2020, 2020-2021,
2021-2022, 2022-2023, 2023-2024, 2024-2025) — las URLs de los 6 ya estaban verificadas a mano
desde antes (ver cabecera de `extractor_formato911_historico.py`), y solo 3 se habían corrido
contra `_parsear_ciclo` con datos reales dentro de esta sesión. Se volvió a correr `_parsear_ciclo`
contra los 6 CSV reales de Diana (`~/Downloads/`) para cerrar la evidencia:

| Ciclo | Filas | `matricula_total` no numérico |
|---|---|---|
| 2019-2020 | 230,424 | 0 |
| 2020-2021 | 228,852 | 0 |
| 2021-2022 | 228,804 | 0 |
| 2022-2023 | 229,691 | 0 |
| 2023-2024 | 231,534 | 0 |
| 2024-2025 | 231,913 | 0 |

Los 6 parsean limpio con la misma función real del extractor, sin adivinar columnas. Actualizado
en `DS-01_Formato_911.md` §9, y el comentario de cabecera de
`src/ingesta/extractor_formato911_historico.py` (ya no dice "3 comparados, 3 asumidos").

## PR abierto y decisión sobre SNIEE (2026-08-22)

- Diana pusheó `feat/diana-varela-matricula-historica-risk007` y abrió el PR con el título
  "RISK-007/DEC-007: pipeline aislado de matrícula histórica multi-ciclo (Bronze→Silver→Gold)",
  usando la plantilla completa de `.github/PULL_REQUEST_TEMPLATE.md`. Reviewer: @edgarcoroneln
  (DEC-003, compuerta única).
- **Corrección adicional sobre la sección "Avance entregado":** la vía de la serie SNIEE no se
  descartó por no existir — el sitio `snie.sep.gob.mx` estaba **caído por falla de DNS** al
  momento de intentar acceder, así que nunca se pudo confirmar si la serie existe ahí. Diana ya
  había propuesto por Teams (con Héctor y Edgar) usar el microdato real del 911 multi-ciclo en
  vez de esperar a SNIEE, y el equipo lo acordó — este PR entrega exactamente esa decisión ya
  tomada, no un hallazgo nuevo de esta sesión. Corregido en `DS-01_Formato_911.md` §9/§9a y en
  la descripción del PR.
- Mensaje enviado a Teams anunciando el cierre a Héctor (con el link del PR), explicando también
  la falla de DNS de SNIEE.

## Revisión de estado general de Diana (US-101 a US-106) y PR #31/#63

A petición de Diana, se revisó qué le falta de sus 6 historias y si sus bloqueantes previos ya se
resolvieron:

- **US-101 a US-105: `done`** (ver `Execution_Status.md`). **US-106** ("Congelar esquema y
  documentar linaje completo", S5) sigue `⬜ Por iniciar`, vence el 6 de septiembre.
- Su tabla de autoseguimiento en `12_Roadmap_Sprints/Sprints/1-diana-aracely-alvarez-varela.md`
  §9 está **desactualizada** (todavía marca US-103/104/105/106 en 0% y un bloqueo de
  `docker-compose.yml` en US-102 ya resuelto) — pendiente que ella la actualice antes del próximo
  standup.
- **RISK-004** (suyo) — `cerrado`. **RISK-002** (suyo) — sigue `mitigando`, pero lo pendiente
  (DS-06/DS-08) es de Emilio, no de ella.
- **PR #31** (Luis E. García, US-121b/122b): DS-04 (SESNSP) sigue bloqueada — el enlace oficial
  redirige al login de Microsoft/SharePoint; dos alternativas ya probadas y fallidas
  (`datos.gob.mx` CKAN → 403 Akamai; `secretariadoejecutivo.gob.mx` → sin conexión). Luis lo
  escaló a Diana el 14-ago y volvió a recordarlo el 21-ago. **Decisión tomada por Diana:** buscar
  otra fuente pública equivalente para incidencia delictiva municipal, en vez de pelear con el
  login de SharePoint. Comunicada a Luis en el PR #31.
- **PR #63** (Luis E. García, US-123b, Great Expectations para DS-05): encontró que 24/384
  estaciones SINAICA (≈6.3%) traen lat/lon inutilizable — 3 `NULL` genuinos y 21 con el
  placeholder literal `"0.0"` en vez de `SIN_DATO`. Preocupación: que el IDW de US-105 (Diana,
  19-ago) jale esas coordenadas `(0,0)` hacia el cálculo de escuelas cercanas.
  - **Análisis:** revisando `fact_escuela_ciclo.sql`/`features_escuela.sql`, los 3 `NULL` ya
    estaban filtrados (`latitud is not null and longitud is not null`). Las 21 estaciones con
    `"0.0"` no llegaban a corromper el resultado porque el filtro de radio (`distancia_km <= 15`)
    ya las excluía de facto — ninguna escuela de México cae a <15km de `(0,0)` — pero era
    "correcto de casualidad" (por geografía), no por diseño explícito.
  - **Fix aplicado:** se agregó `and latitud != 0 and longitud != 0` al filtro de la CTE
    `aire_pm25` en ambos modelos, para no depender de la geografía (regla del proyecto,
    `Data_Model.md` §3: "SIN_DATO explícito, nunca cero ni nulo silencioso").
  - **Validado real:** `dbt build --select fact_escuela_ciclo features_escuela` contra Postgres
    real → **26/26 tests PASS, 0 errores**. Confirmado además a nivel SQL que
    `cast('0.0' as double precision) != 0` da `false` en Postgres — el filtro sí excluye el
    placeholder.
  - Respuesta enviada a Luis en el PR #63 confirmando el hallazgo, el análisis y el fix.

## Reconciliación BUG-008 → BUG-009 (2026-08-22, tras revisión de `origin/main`)

- El bug de las 7/10 fuentes Bronze sin `identifier` (documentado arriba como "BUG-008" en el
  momento de esta sesión) **colisionó** con otro BUG-008 preexistente, distinto y de otra rama
  (`docker/api.Dockerfile` arrancando `src.api.main:app` — el "hola mundo" de US-501 — en vez de
  `src.api.app:app`, la app real del contrato v1; bloquea US-401/402/411).
- Edgar resolvió la colisión directamente en `main` (commits `c3af546`/`3b407d8`, 2026-08-22
  15:17–15:20): el bug de docker se queda como **BUG-008**, y el bug de Diana (sources.yml) se
  **renumera a BUG-009**. Fila actual en `Bug_Register.md`:
  `BUG-009 | 7 de 10 fuentes Bronze en sources.yml sin identifier por default... | high | open |
  US-111 | pendiente (Edgar decide reparto)`.
- Todas las referencias a "BUG-008" de este DevLog para este hallazgo se corrigieron a BUG-009
  arriba. El único open item real es el mismo de siempre: reparto/fix pendiente, ahora bajo el
  ID correcto.

## Fix D6 IDW aplicado, pendiente de push (2026-08-23)

- El fix del hallazgo de Luis (PR #63, sección arriba) — `and latitud != 0 and longitud != 0`
  en `fact_escuela_ciclo.sql` y `features_escuela.sql`, validado 26/26 tests PASS — se aplicó y
  documentó en sesión, pero **Diana pausó antes de comitearlo y pushearlo**. La rama original
  (`feat/diana-varela-matricula-historica-risk007`) ya se mergeó como PR #68 y se borró de
  `origin`, así que este fix sale en una rama nueva.
- Verificado contra `origin/main` (`711840b`, con PR #63/#69/#70/#71/#72 ya mergeados desde el
  PR #68 de Diana): ningún PR posterior tocó `fact_escuela_ciclo.sql` ni `features_escuela.sql`
  — el fix aplica limpio, sin conflictos.
- Nota informativa (no bloqueante): PR #72 (Deni, US-112) resolvió formalmente la duda pendiente
  de `ciclo` vs `id_ciclo` en `dim_tiempo.sql` — queda como decisión canónica coordinada en
  US-111, ya no es ambigüedad abierta.
- Nota de proceso: PR #69 (Edward Bustillos) agregó `.github/workflows/quality_gate.yml` —
  todo PR nuevo hacia `main` ahora falla en CI si la descripción deja alguna casilla `[ ]` sin
  marcar en la plantilla, y corre `vault_lint.py`. Aplica al PR de este fix.

## Próximos pasos
- Comitear y pushear el fix D6 (`fact_escuela_ciclo.sql`/`features_escuela.sql`) + este DevLog
  actualizado desde una rama nueva, y abrir PR (ver sección arriba).
- Actualizar `12_Roadmap_Sprints/Sprints/1-diana-aracely-alvarez-varela.md` §9 (tabla de
  autoseguimiento) para reflejar el estado real de US-101 a US-106.
- Agregar fila en la Traceability Matrix para este PR.
- Considerar con Edgar si vale la pena una nota corta al equipo sobre la pérdida de estado
  entre sesiones (ver "Continuación" arriba) — no bloquea nada de RISK-007, pero es información
  útil si le vuelve a pasar a alguien más.
- Esperar respuesta de Luis en PR #31 sobre una fuente alterna para DS-04 (incidencia delictiva).
- Empezar US-106 (congelar esquema y documentar linaje completo), vence 6 de septiembre.