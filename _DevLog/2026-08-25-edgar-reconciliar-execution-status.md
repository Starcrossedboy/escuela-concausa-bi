---
project: "FARO"
date: "2026-08-25"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "claude-opus-5"
session_duration: "media — reconciliación de Execution_Status contra lo mergeado en main"
touches: ["US-004", "US-106", "US-111", "US-112", "US-113", "US-123b", "US-201", "US-203", "US-211b", "US-302", "US-311", "US-313", "US-411", "US-522c", "US-523c", "PLAN-EXEC-STATUS", "RISK-003", "RISK-006"]
tags: [devlog, pm, gobernanza, tablero]
---

# DevLog — 2026-08-25 — Reconciliar `Execution_Status` con lo entregado

→ [[_DevLog/_index|Volver al índice]] · [[12_Roadmap_Sprints/Execution_Status]] · [[13_Reports/PM_Dashboard_Spec]]

## Contexto

Varios integrantes reportaron que el tablero PM los muestra con historias pendientes que ya
entregaron. Tenían razón: `Execution_Status.md` no se actualizaba desde el **21 de agosto** y desde
entonces se habían mergeado **20 PRs**.

## Qué se corrigió

Se cruzó cada historia contra tres fuentes independientes: los PRs mergeados, el DevLog de quien la
entregó y el `status` de los documentos canónicos que produce (`15_ML_Models/*`,
`08_CICD_DevOps/*`, `03_Architecture/*`). **Ocho historias** cambiaron de estado:

| Historia | Antes | Ahora | Por qué |
|---|---|---|---|
| `US-112` | `in_progress` | **`done`** | El propio DevLog de Deni condicionaba el cierre a que PR #72 dejara de estar abierto; se mergeó el 22-ago |
| `US-203` | ausente | **`done`** | PR #71 — filtros AC-002.2 completos, nombres INEGI reales, 47 casos y E2E 16/16 charts |
| `US-211b` | ausente | **`done`** | PR #73 aprobado por Manuel + PR #78 (KPI-19/20) cierra §8.3 |
| `US-523c` | ausente | **`done`** | PR #69; el documento de la historia ya decía `status: done` |
| `US-302` | `in_progress` | **`in_review`** | PR #58 integró ML-02 con SHAP, pero `ML02_Clasificacion_Driver` sigue `in_review` |
| `US-313` | `in_progress` | **`in_review`** | PR #83 implementó el grano dual de DEC-010, pero `Publicacion_Gold` sigue `in_review` y BUG-010 mantiene `/predicciones` en `mock_data` |
| `US-411` | ausente | **`in_review`** | PR #59 mergeado, pero Karla la declara al 90% y `/series` quedó fuera de alcance |
| `US-106` | ausente | **`in_progress`** | PR #77 documentó el linaje, pero **el freeze no está declarado**: el documento sigue en `draft` |

Se enriqueció además la evidencia de `US-111`, `US-113`, `US-123b`, `US-201` y `US-522c` sin cambiar
su estado, porque ya la tenían correcta pero incompleta.

## Dos historias que SÍ estaban bien reportadas

Vale registrarlo porque el primer barrido las marcó como error y no lo eran:

- **`US-123b`** — un PR mergeado la citaba (#63), pero solo cubre la mitad DS-05. La mitad DS-04 sigue
  abierta en PR #85. `in_progress` al 50% es correcto.
- **`US-311`** — PR #56 implementó el target híbrido, pero sobre *fixture*: el objetivo real depende de
  la serie SNIEE (gate 30-ago) y falta confirmar el registry de MLflow. `in_progress` es correcto.

La lección para el próximo barrido: **que un PR mergeado cite una historia no significa que la
cierre.** Hay que leer qué entregó, no qué mencionó.

## Una corrección al diagnóstico inicial

El primer análisis reportó como falla que `Execution_Status` registrara "solo 43 de 95 historias".
**No es una falla**: la línea 21 del propio documento establece que toda historia ausente se
interpreta como `planned`, precisamente para no duplicar el catálogo de `User_Stories.md`. Las
ausentes son mayoritariamente historias que no han empezado. El defecto real era más chico y más
concreto: ocho historias cuyo estado cambió y nadie lo registró.

## Efecto en el tablero

| | Antes | Después |
|---|---|---|
| `done` | 21 | **25** |
| `in_review` | 3 | **6** |
| `in_progress` | 19 | 17 |
| `planned` | 48 | 43 |

## La causa de fondo, que este PR no resuelve

`Execution_Status` lo actualiza el PO al cierre de cada standup, y se atrasó cuatro días. Pero hay una
segunda fuente de ruido, independiente: **13 de los 21 planes de sprint no se han tocado desde el 9 de
agosto**, día uno del proyecto, pese a que cada plan pide actualizar su tabla §9 antes de cada
standup. El caso extremo es Héctor: su tabla nunca se ha actualizado y lleva cuatro PRs mergeados
(#56, #70, #83, #86), incluido el contrato de grano dual de DEC-010.

Mientras esas tablas no se llenen, el PO tiene que reconstruir el estado leyendo PRs uno por uno —
que es exactamente lo que se hizo hoy. Alimenta **RISK-003** (participación no auditable) y
**RISK-006** (el vault pierde trazabilidad con 21 contribuidores).

## Uso de IA

- **Archivos modificados:** `12_Roadmap_Sprints/Execution_Status.md`, `_DevLog/_index.md`, este archivo.
- **Decisiones autónomas del agente:** ninguna de fondo. El agente hizo el cruce entre PRs mergeados,
  DevLogs y `status` de documentos canónicos, y propuso el estado de cada historia; cada propuesta se
  sostiene en evidencia citada en la tabla. Donde la evidencia era ambigua se eligió el estado **más
  conservador** (`in_review` en vez de `done` para US-302, US-313 y US-411).
- **Correcciones manuales:** el agente marcó inicialmente `US-123b` y `US-311` como mal reportadas;
  al revisar el alcance real de sus PRs resultó que su estado era correcto y se dejaron sin cambio.
  También sostuvo que registrar 43 de 95 historias era un defecto, hasta que se leyó la regla de la
  línea 21 del propio documento.

## Seguridad / calidad

- [x] `python _Meta/scripts/generate_pm_dashboard.py .` — 91 US, 21 personas, 8 fuentes
- [x] `python _Meta/scripts/validate_pm_dashboard.py .` — TEST-002 válido
- [x] `python _Meta/scripts/vault_lint.py .` — Vault limpio
- [x] **Los archivos generados del tablero NO van en este PR.** Al regenerar en local sin token de
      GitHub, `collect_github_activity.py` no corre y la pestaña Engagement queda degradada. Fase B
      los reconstruye con token al mergear (DEC-004), y el job del CI regenera desde fuentes
      canónicas, así que no exige que el HTML commiteado coincida.
- [x] Solo documentación de gobernanza; no se tocó código ni configuración

## Próximos pasos

- **Los 13 planes de sprint sin actualizar.** Sin eso, esta reconciliación se repite cada semana.
- **Karla (US-411):** confirmar si cierra al 100% con `/series` fuera de alcance o qué falta.
- **Célula 3 (Andrés, Héctor):** `ML02_Clasificacion_Driver` y `Publicacion_Gold` siguen en
  `status: in_review`; pasarlos a `approved` cierra US-302 y US-313.
- **Deni (US-113):** es el ítem que falta para que Diana pueda declarar el freeze de US-106.
