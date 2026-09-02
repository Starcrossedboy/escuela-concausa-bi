---
id: RPT-JUNTA-MOCK-2026-08-29
title: "Guion de la junta del mock — corte del 29 de agosto de 2026"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: false
traces_up:
  - "vault/12_Roadmap_Sprints/Execution_Status"
  - "vault/06_Quality_Testing/Bug_Register"
  - "vault/13_Reports/Vault_Correcciones_2026-08-29"
traces_down:
  - "vault/03_Architecture/ADRs/ADR-007-unidad-target-variacion-matricula"
last_reviewed: "2026-08-29"
tags: [report, meeting, mock, ensayo-e2e, pm]
---

# Guion de la junta del mock — 29 de agosto de 2026

> Corte tras **14 PRs mergeados en un día**. La fuente canónica del estado sigue siendo
> [[vault/12_Roadmap_Sprints/Execution_Status]]; este documento existe para conducir la junta y salir con
> tres decisiones tomadas.
> → [[vault/06_Quality_Testing/Bug_Register]] · [[vault/13_Reports/Vault_Correcciones_2026-08-29]]

## 1 · Respuesta corta a «¿podemos hacer el mock hoy?»

**Sí, con una salvedad que hay que decir en voz alta al principio y no al final.**

| Se puede demostrar hoy | Estado |
|---|---|
| Pipeline completo Bronze → Silver → Gold sobre datos reales | ✅ 4 ciclos reales, estrella y 8 cubos, 149/149 pruebas dbt |
| Tableros leyendo de Gold real | ✅ DB-01, DB-02, DB-03, DB-05, DB-08 |
| Los 3 modelos ML entrenando y registrados en MLflow | ✅ ML-01, ML-02, ML-03 |
| Agente conversacional con guardarraíles | ✅ RAG integrado, `SELECT INTO` bloqueado |
| Suite de pruebas | ✅ **589 passed**, 5 skipped |

| **No** se puede demostrar hoy | Por qué |
|---|---|
| **Cualquier ruta de la API sobre la URL pública** | **BUG-020**: toda ruta que toca base de datos responde 500 |

**Esa es la única grieta, y es la que la rúbrica castiga más:** sin URL pública funcionando, la nota
máxima es 6.0. El mock puede correr entero en local; la demo final, no.

## 2 · Lo que cambió hoy

**14 PRs mergeados.** Se cerraron 6 historias y 3 bugs; se levantó 1 bug nuevo.

| Cerradas hoy | Quién |
|---|---|
| `US-121a` `US-122a` `US-123a` `US-124a` — DS-06 y DS-08 | Emilio Galnares |
| `US-213` — DB-05 (6 tabs) y DB-08 (explorador) | Monserrat Miranda |
| `US-221` — gráficos base de KPIs | Oscar Quiroz |
| `US-322` — EDA y selección de variables | Estefany Hernández |

| Avanzaron sustancialmente | Detalle |
|---|---|
| `US-212` | 90% → **95%**. BUG-026 cerrado; único bloqueo: ratificar ADR-007 |
| `US-321` | ML-03 entrenado **y** registrado en MLflow |
| `US-325` | `cve_mun` en el contrato, con tres PRs coordinados sin romperse entre sí |
| `US-303` | Los tres modelos se registran por el mismo camino |
| `US-222` | Capa de datos de DB-07 lista y validada contra Postgres real |

| Bugs | Movimiento |
|---|---|
| **BUG-026** | `fixed` — fixture de 4 ciclos sobre las CCT del catálogo (Diana, verificado por Marina) |
| **BUG-027** | `superseded` — el follow-up de US-221 borra los archivos que había que corregir |
| **BUG-018** | `fixed` — corregido desde el 28-ago; el registro iba detrás de la matriz |
| **BUG-028** | **nuevo y ya corregido** — el cero de `cve_mun` se perdía en el lector de producción |

## 3 · Decisión 1 — Ratificar ADR-007 · **la más importante de la semana**

**Es la única decisión que desbloquea trabajo de tres personas a la vez.**

`target_variacion_matricula` se está produciendo en **dos unidades bajo el mismo nombre**:
`features_escuela.sql` da alumnos absolutos y `target_hibrido` da fracción. Ambas escriben en la
misma columna de `gold.predicciones`.

### El dato que cambia la conversación

`DEC-006`, ratificada por Manuel Serranía el **13 de agosto**, dice:

> «escuela en riesgo = `indice_riesgo ≥ 0.6` ↔ pérdida de **~5 % de matrícula**»

Ese «~5 %» **es una fracción**. El umbral que Célula 2 ya usa en sus tableros sólo significa algo si
el target lo es.

**Por lo tanto la junta no decide una unidad nueva: decide si alinea el código con una decisión que
el equipo ya tomó hace dos semanas.** Quien empuje la alternativa A (alumnos absolutos) está
proponiendo **reabrir DEC-006**, y conviene que se diga con ese nombre.

### Qué está en juego

| Si se ratifica **fracción** | Si no |
|---|---|
| `DEC-006` y el umbral 0.6 siguen válidos | Hay que rehacer **§5.1** del contrato de DB-03/DB-04 |
| Marina verifica AC-002.4 y cierra US-212 al 100% | US-212 se queda en 95% medio sprint más |
| BUG-017 y BUG-019 se cierran solos | Siguen abiertos |
| Coste: minutos | Coste: medio sprint de Célula 2 |

**Mesa:** Andrés González (modelado), Christian Ruiz (contrato de API), Diana Alvarez (producción en
Gold), Marina García (consumo en tableros). Convoca: Edgar Coronel.

> Marina entró a la mesa a petición propia y con razón: el rechazo de la alternativa B se apoya
> textualmente en que «Superset lee Gold directo». Héctor lo dejó escrito en el ADR como **defecto
> del artefacto, no omisión de cortesía**. Vale citarlo en la junta: es el estándar que queremos.

**Protección vigente:** Héctor puso una guarda que detiene la publicación en vez de saturar en
silencio. Hoy estamos protegidos, pero el bloqueo sigue.

## 4 · Decisión 2 — BUG-020 · qué hacemos si no se resuelve

**Severidad crítica. Es el único riesgo vivo para la casilla 6 del ensayo E2E y para 1.0 punto de la
rúbrica.**

En la URL pública, `/api/v1/predicciones/{cct}`, `/predicciones/batch` y `/escuelas` responden **500**.
`/api/v1/health` responde 200, así que el contenedor corre. Con token válido, inválido o sin token el
resultado es el mismo 500 — **nunca 401** —, así que el fallo ocurre *antes* de validar auth. Eso
apunta a la sesión de base de datos, no a la autenticación.

**Lleva abierto desde el 27-ago y se pidió estado dos veces sin respuesta.**

**Lo que la junta tiene que decidir, no discutir:**

1. Christian y Luis dan una **hora concreta** de diagnóstico, no un «ya casi».
2. Si a esa hora no hay causa raíz identificada, **se activa el plan B por escrito**: el mock se
   demuestra en local, se registra como deuda de S5 y se comunica al evaluador como limitación
   conocida en vez de descubrirse en vivo.
3. Se nombra a **una sola persona** responsable de reportar avance cada 2 horas hasta cerrarlo.

## 5 · Decisión 3 — El choque de DB-05 (PR #134)

**Manuel y Monserrat tienen un conflicto real que ninguna herramienta resuelve.**

El repunteo de US-205 re-escala DB-05 a KPI-07 y saca `valor_promedio_driver` del catálogo de
métricas. El tablero DB-05 de Monserrat, ya mergeado, **la usa en 18 charts**. Al mergear se cae
`test_todo_chart_de_db05_apunta_a_dataset_y_metrica_declarados` — que es la guarda funcionando
correctamente.

Manuel ramificó antes de que entrara el PR #114, así que no había forma de que viera esos 36 charts.
**No es descuido de nadie.**

**Dos salidas, y hay que elegir una hoy:**

- **A.** El catálogo conserva `valor_promedio_driver` junto a KPI-07 → los 18 charts no se tocan.
- **B.** Los 18 charts de DB-05 se repuntan a la métrica nueva → la convención queda limpia.

Manuel es dueño de la convención (US-202/US-205); Monserrat, del tablero (US-213). **Urge porque el
repunteo cambia la convención de los 10 tableros** y Marina lleva días esperando saber si le toca
rehacer los SQL de DB-03/DB-04.

## 6 · Lo que quedó atorado y no depende de nosotros

| PR | Autor | Bloqueo | Espera a |
|---|---|---|---|
| **#102** | Alejandro Velázquez | Todo resuelto salvo una firma | **Luis Téllez** — Approve por regla 7 (toca el CMD del contenedor) |
| **#87** | Edgar Ulises Jiménez | **3 días sin un commit.** Conflictos ya resueltos por el PM | **Él** — renombrar su ADR a `ADR-008` (hoy colisiona con el de Héctor, regla 3) y marcar las casillas del PR, que son su declaración de lo que probó |
| **#134** | Manuel Serranía | Choque con DB-05 | Acuerdo Manuel ↔ Monserrat (§5) |
| **#130** | Diana Alvarez | Ninguno | Se cierra: quedó redundante |

## 7 · Riesgo que nadie ha nombrado — DS-07

**`DS-07` (CONEVAL) sigue en `status: draft` con la prueba de descarga marcada como pendiente desde
la Semana 1. Estamos en la quinta.**

No es una fuente más de las ocho: **alimenta D1, pobreza y rezago social**, el primer driver y uno de
los dos con cobertura nacional. Sin dato real, el driver dominante por escuela se calcula sobre cinco
drivers en vez de seis, y **la recomendación prescriptiva —el diferenciador del proyecto— pierde la
dimensión de mayor peso en el target**.

Lo encontró Diana de rebote: `gold.dim_municipio` cubre **10 municipios** porque `bronze.coneval`
sigue con la muestra de prueba. Efecto colateral: varios tests de `relationships` están en verde
contra un universo diminuto — el mismo modo de falla de BUG-012 y BUG-026, donde una tabla casi vacía
pasa cualquier prueba.

**Decisión que hay que tomar hoy, no el 6 de septiembre:** o Deni ejecuta la descarga, o se registra
el bloqueo con ID, o se documenta D1 como cobertura parcial explícita con su bandera `SIN_DATO`. Las
tres son defendibles ante el evaluador. Lo que no es defendible es que aparezca el día de la demo.

## 8 · Patrón técnico que vale contar en la junta

**Tres defectos distintos, la misma causa, en 48 horas.** Todos aparecieron al incorporar `cve_mun` al
contrato de `gold.features_escuela`:

| Dónde | Qué se rompió |
|---|---|
| PR #127 | La invariante de DEC-007: la agregación daba 230 filas contra 315 |
| **BUG-028** | El cero de `cve_mun` se perdía en el lector de producción |
| PR #131 | Un test que heredaba del fixture la ausencia de la columna, y dejó de comprobar nada |

Los tres artefactos **asumían algo del entorno en vez de declararlo**. Ninguno estaba mal escrito;
simplemente nadie tenía forma de saber quién dependía de que la columna **no** existiera.

**Criterio que propongo adoptar:** cuando un contrato incorpora un campo, se busca activamente todo lo
que asumía su ausencia. Y las pruebas construyen su propia precondición en vez de heredarla de un
fixture compartido.

Vale decirlo en la junta porque **el sistema funcionó**: las tres las atrapó una guarda, no un
usuario. Eso es lo que hay que presumir, no esconder.

## 9 · Agenda sugerida — 45 minutos

| Min | Tema | Salida esperada |
|---|---|---|
| 0-5 | Estado: 14 PRs, 6 historias cerradas, 589 pruebas | Contexto |
| 5-20 | **ADR-007** — con el dato de DEC-006 sobre la mesa | **Decisión ratificada** |
| 20-30 | **BUG-020** — hora concreta o plan B | **Responsable y hora** |
| 30-38 | **DB-05** — Manuel ↔ Monserrat, opción A o B | **Opción elegida** |
| 38-45 | DS-07 y cierre | **Deni responde: descarga, bloqueo o cobertura parcial** |

**Si sales de la junta con esas cuatro cosas, el mock del 6 de septiembre es viable.** Si sales sin
ADR-007, US-212 no cierra y DB-04 va a mostrar «100 % de escuelas en riesgo» — un número creíble que
está mal, que es exactamente el tipo de error que este proyecto existe para no cometer.
