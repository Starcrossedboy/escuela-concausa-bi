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

## Uso de IA

- **Archivos modificados:** `05_Engineering/Branch_Protection.md`,
  `12_Roadmap_Sprints/Execution_Status.md`, `_DevLog/_index.md`, este archivo.
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
