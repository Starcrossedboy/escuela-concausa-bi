---
project: "FARO"
date: "2026-08-26"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "larga — desbloqueo de 6 PRs, reconciliación de estado y corrección de Branch_Protection"
touches: ["PLAN-EXEC-STATUS", "DOC-BRANCHPROT", "US-106", "US-113", "US-122b", "US-123b", "US-124b", "US-203", "US-212", "US-522a", "US-523a", "DEC-003", "REQ-007", "RISK-003", "RISK-006", "RISK-008"]
tags: [devlog, pm, gobernanza, seguridad, tablero]
---

# DevLog — 2026-08-26 — Reconciliación de estado y `Branch_Protection` contra el ruleset real

→ [[_DevLog/_index|Volver al índice]] · [[12_Roadmap_Sprints/Execution_Status]] · [[05_Engineering/Branch_Protection]]

## Contexto

Jornada de desbloqueo: se cerraron **seis PRs** (#80, #81, #84, #85, #88, #90) que llevaban entre uno
y tres días detenidos. Ninguno estaba trabado por su contenido; los seis lo estaban por fricción de
proceso. Este PR recoge las dos consecuencias que quedaron pendientes.

## Parte 1 — `Branch_Protection.md` contra el ruleset real

El PR #90 (US-523a) se mergeó sin las correcciones solicitadas. El documento tiene
`source_of_truth: true` y quedó en `main` afirmando **tres reglas como activas que están apagadas**.

Contrastado contra `GET /repos/{owner}/{repo}/rulesets/{id}`:

| El documento decía | Valor real |
|---|---|
| ☑️ Dismiss stale approvals on new commits | `dismiss_stale_reviews_on_push = false` |
| ☑️ Require conversation resolution before merging | `required_review_thread_resolution = false` |
| ☑️ Do not allow bypassing the above (incluye admins) | `bypass_actors: RepositoryRole admin, mode always` |

**Las tres están apagadas a propósito**, y sin esa explicación el documento invita a "arreglarlas":

- **El bypass de admin sostiene DEC-003.** El PM es el único revisor obligatorio y GitHub no permite
  aprobar el propio PR. Sin bypass, ningún PR del PM podría mergearse jamás.
- **`dismiss_stale_reviews_on_push` apagado** permite que el PM resuelva un conflicto en la rama de un
  compañero sin invalidar la aprobación ya dada. Hoy se usó cinco veces: `main` se movió seis veces en
  un día y las ramas quedaban atrás.

Si alguien alinea la configuración con el documento equivocado, el repositorio se traba por completo.

Se documentan además reglas activas que **nadie había registrado**: `require_code_owner_review`
(lo que hace vinculante a `CODEOWNERS`), los **dos únicos** checks requeridos
(`Calidad de codigo y vault` y `Generar y validar tablero PM` — `quality-checks` y
`Contrato dbt (parse)` corren pero no bloquean), `require_extra_approval_for_unattributed_changes` y
los métodos de merge permitidos. Se incluye el comando para volver a contrastar.

Se restaura el `owner` (el documento es del PM) y se revierten `->` → `→` y `☑️/🔲` → `✅/❌`: el
generador del tablero lee esos emoji, y `❌` significaba "deshabilitado" mientras que `🔲` se lee
como "pendiente".

**No se tocó la configuración del repositorio.** Se ajusta el documento a la realidad, no al revés.

## Parte 2 — Reconciliación de `Execution_Status`

Nueve historias se revisaron contra los PRs mergeados, el auto-reporte de cada dueño en su §9 y el
`status` de los documentos canónicos. **Seis cambian de estado:**

| Historia | Antes | Ahora | Por qué |
|---|---|---|---|
| `US-113` | `in_progress` | **`in_review`** | PR #81 mergeado. Deni la declara `🔵 En revisión 100%`, no terminada: ningún cubo se ha materializado contra la base real |
| `US-123b` | `in_progress` | **`done`** | Las dos mitades entregadas — DS-05 (PR #63) y DS-04 (PR #85) |
| `US-124b` | ausente | **`done`** | PR #85: 28 pruebas offline de extractores y suites GE |
| `US-212` | ausente | **`in_progress`** | PR #84 mergeado, pero Marina la declara al 70%: falta revalidar contra los cubos reales de US-113 |
| `US-522a` | ausente | **`in_progress`** | El PR #90 la declara al 100%, pero **BUG-008** sigue `open`/`high` y es de su propia célula |
| `US-523a` | ausente | **`in_review`** | El documento entró con tres afirmaciones falsas; se corrigen en la Parte 1 |

Se enriqueció la evidencia de `US-106`, `US-122b` y `US-203` sin cambiar su estado.

**Efecto en el tablero:** `done` 25 → **27** · `in_review` 6 → **8** · `in_progress` 17 (sin cambio) ·
`planned` 43 → **39**.

### Dos historias que NO se cerraron pese al PR mergeado

Vale registrarlo, porque es el error recurrente de este registro:

- **`US-113`** — el PR dice "cierra US-113", pero los 9 cubos son `materialized_view` y el CI solo
  corre `dbt parse`. Compilar no es materializar. Además `cubo_pipeline`/DB-10 depende de
  `agua_region`, que lee DS-06, aún sin ingerir.
- **`US-522a`** — el `api.Dockerfile` existe en `main`, sí, pero arranca la app equivocada (BUG-008).
  Que el entregable exista no significa que funcione.

## Validaciones pendientes y quién las cierra

| Historia | Qué falta | Quién valida |
|---|---|---|
| `US-113` | Materializar los 9 cubos contra la base real (`dbt run --select gold`) | **Diana Alvarez** (TL C1) |
| `US-212` | Revalidar DB-03/DB-04 contra los cubos reales, ya no sobre mock | **Marina García**, con Manuel Serranía (TL C2) |
| `US-523a` | Aprobar el documento corregido | **Edgar Coronel** (PM) |
| `US-302` | Pasar `ML02_Clasificacion_Driver` de `in_review` a `approved` | **Andrés González** (TL C3) |
| `US-313` | Pasar `Publicacion_Gold` a `approved`; depende de BUG-010 | **Héctor Morales** (C3) |
| `US-411` | Confirmar si cierra al 100% con `/series` fuera de alcance | **Karla Monter** (C4) |
| `US-521c` · `US-522c` | Escribir el DevLog que falta para `done`; BUG-004 sigue abierto | **Edward Ulysses Ruiz** (C5) |
| `US-004` | Cerrar la matriz como mantenida | **Edgar Coronel** (PM) |
| `US-106` | Declarar el freeze: exige US-113 cerrada y RISK-008 confirmado | **Diana Alvarez**, con Deni Garrido |

## Un plan de sprint que describía mal su propia historia

Juan Carlos Macías terminó **US-415** y, antes de escribir una línea de US-412, preguntó en vez de
asumir. Tenía razón en las dos cosas que levantó.

**Su plan pedía inferencia viva.** El objetivo de US-412 decía *"rutas que cargan los 3 modelos desde
MLflow y devuelven predicción"*. Se redactó el **31 de julio**, antes de **DEC-010** y de US-313:
entonces no existía publicación batch a Gold y esa era la única vía imaginable. Hoy
`gold.predicciones` y `gold.recomendaciones` están pobladas y verificadas contra Postgres, y
**BUG-010** ya documenta el mapeo campo por campo desde SQL. Se corrigió el objetivo a lectura de
Gold con `RepositorioModelos`, mismo patrón `Depends` + doble de prueba que `repositorio_gold.py`.
**US-416 heredaba la premisa** —"respuesta degradada si un modelo no responde"— y se corrigió
también: sin inferencia viva, eso pasa a significar que la tabla no trae fila, y la degradación
correcta es `SIN_DATO`, no un valor inventado.

Queda escrito en el plan que leer tablas precalculadas **no** debilita el "3 modelos integrados vía
API" de la rúbrica: `gold.predicciones.mlflow_run_id` conserva el enlace auditable a la corrida de
MLflow que produjo cada valor.

**`PrediccionOut.cluster` es un `StrictInt` obligatorio sin productor.** ML-03 (US-321, Estefany
Hernández) no existe todavía. El BUG-010 ya lo señalaba y lo dejaba a decisión de Célula 4. La
decisión **no era nueva**: Christian Ruiz sentó el precedente el **20 de agosto**, cuarenta líneas
más arriba en el mismo archivo, al hacer `EscuelaOut.indice_riesgo` y `driver_dominante` opcionales
con `None => SIN_DATO explícito, nunca inventado`. `cluster` sigue ese patrón: `StrictInt | None`.
**Sin bandera de cobertura acompañante**, a diferencia de `tiene_prediccion`: ahí la ausencia varía
por escuela, aquí ML-03 no existe para nadie y la bandera sería `False` constante.

El cambio toca el contrato público, así que el PR de US-412 exige aviso a **C2** y **C3** por la
regla de oro de [[03_Architecture/API_Specification]], y suma a **Karla Monter** por ser la dueña
de ese documento. Arrastra además `tests/test_api_contract.py:160`
(`assert isinstance(cuerpo["cluster"], int)`, que fallará con `None`) y `src/api/mock_data.py:138`,
que hoy fabrica el cluster con `int(cve_mun[:2]) % 4` — el entero inventado que haría pasar la
verificación #4 del ensayo de forma engañosa.

**Lo que este PR no toca:** la tabla §9 de su plan. La actualiza el dueño antes de cada standup; el
PM corrige el alcance que el PM redactó mal, no reporta el avance ajeno.

## Una historia asignada a alguien que no tenía nada que escribir

**US-421** ("esqueleto de FastAPI y healthcheck", Eloisa González Rubio, S3) **ya estaba entregada
antes de que ella arrancara**, y por dos personas distintas:

| Mitad | Quién | Evidencia |
|---|---|---|
| Esqueleto FastAPI | **Luis Téllez** | `src/api/main.py` · `0bfeb2e` · 09-ago · US-501 día 1 |
| Healthcheck + contrato navegable | **Christian Ruiz** | `src/api/v1/health.py` + `src/api/app.py` · `1648259` · PR #19 · 11-ago · US-401 |

`/health`, `/version` y `/api/v1/docs` —o sea AC-004.1— existen y están cubiertos por `test_health_ok`
y `test_version_ok` en `tests/test_api_contract.py`, ambas en verde. Eloisa lo verificó de punta a
punta, incluido un proxy corporativo que interceptaba `localhost`, y lo dejó en dos DevLogs (PR #91).
**Sin código propio, porque no quedaba código por escribir.**

Se registra `done` **con la autoría explícita en la evidencia**. Que la historia esté cumplida no
autoriza a acreditársela a quien no la escribió: la columna nombra a Luis y a Christian con su commit.
Es la contraparte de la regla que ya rige este registro —un PR mergeado que cita una historia no la
cierra— aplicada al revés: una historia cerrada no acredita a su dueña nominal.

**El error es del PM**, y conviene dejarlo escrito: se asignó una historia de S3 sin verificar que dos
historias de S1 y S2 ya la cubrían. Eloisa se reasigna a **US-422** (pruebas de la API, ya suya),
arrancando por la prueba que detecta **BUG-008** — hoy **ninguna prueba verifica qué aplicación
arranca el contenedor**, que es exactamente por lo que ese bug sobrevivió hasta bloquear el ensayo
E2E del 28–29.

Alimenta **RISK-003**: durante dos semanas el tablero mostró como pendiente una historia entregada, y
a una integrante como sin avance mientras verificaba trabajo ajeno.

## Uso de IA

- **Archivos modificados:** `05_Engineering/Branch_Protection.md`,
  `12_Roadmap_Sprints/Execution_Status.md`,
  `12_Roadmap_Sprints/Sprints/4-juan-carlos-macias-mayen.md`, `_DevLog/_index.md`, este archivo.
- **Decisiones autónomas del agente:** ninguna de fondo. El agente consultó la API de rulesets,
  cruzó cada historia contra PRs mergeados / auto-reporte / `status` de documentos canónicos, y
  propuso estado y evidencia. Donde el dueño declaraba 100% pero la evidencia no lo sostenía se
  eligió el estado **más conservador** (`in_review` para US-113 y US-523a; `in_progress` para
  US-522a y US-212), dejando escrito el motivo y el validador.
- **Correcciones manuales:** el agente propuso primero aplicar la corrección de `Branch_Protection`
  dentro del PR #90; se mergeó antes, así que se rehízo sobre `main`. También construyó un script de
  fusión de la matriz de trazabilidad que en su primera versión **truncaba** el aporte de un
  compañero: se detectó al verificar, se reescribió anclando en la base y se le agregó una guarda que
  aborta sin escribir si detecta pérdida.

## Seguridad / calidad

- [x] `python _Meta/scripts/vault_lint.py .` — Vault limpio
- [x] `python _Meta/scripts/generate_pm_dashboard.py .` — 91 US, 21 personas, 8 fuentes
- [x] `python _Meta/scripts/validate_pm_dashboard.py .` — TEST-002 válido
- [x] 52 filas en `Execution_Status`, sin duplicados y con las 8 columnas correctas
- [x] **No se tocó la configuración del repositorio ni ninguna credencial**
- [x] Los archivos generados del tablero **no van en este PR**: Fase B los reconstruye con token al
      mergear (DEC-004) y el CI los regenera desde las fuentes canónicas

## Lo que este PR no resuelve

- **Seis integrantes siguen sin un solo commit en `main`**: Emilio Galnares (DS-06/DS-08), Estefany
  Hernández, Carlos Mayorga, Juan Carlos Macías, Oscar Quiroz y Eloisa González (con su primer PR
  abierto, el #91). Alimenta **RISK-003** y **RISK-006**.
- **12 de los 21 planes de sprint no se tocan desde el 9 de agosto**, día uno. Mientras esas tablas
  §9 no se llenen, el PO reconstruye el estado leyendo PRs uno por uno — que es lo que se hizo hoy.
- **`quality_gate.yml` no escucha el evento `edited`** y busca `[ ]` en todo el cuerpo del PR, no solo
  en casillas de lista. Hoy dio falso rojo en los PR #84 y #88. Costó los PR #73, #78, #79, #84 y #88.
- **Las cabeceras de `requirements/celula-*.txt`** indican correr `pip freeze > requirements/celula-N.txt`,
  lo que destruye el archivo curado. Es exactamente lo que pasó en el PR #91.
