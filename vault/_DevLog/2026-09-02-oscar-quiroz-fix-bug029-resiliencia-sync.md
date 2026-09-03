---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión única: fix de BUG-029 tras confirmación de Edgar Coronel"
touches: ["US-222", "US-223", "US-205", "BUG-029", "REQ-002"]
tags: [devlog]
---

# DevLog — 2026-09-02 — Fix de BUG-029: el sync ya no aborta toda la corrida

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué pedí

Un comentario en el PR #192 me indicaba que BUG-029 era mi siguiente paso, pero el propio
`Bug_Register.md` decía que la "solución de fondo" era de Manuel (US-205). Le pregunté a Edgar
directamente por Teams para no chocar con el trabajo de otra persona sin confirmar. Edgar
respondió explícitamente: **"si es tuyo... tu US NO está terminada... debes cerrar esa parte del
bug-029"**. Con esa confirmación de la compuerta única (DEC-003), pedí implementar el arreglo.

## Qué hizo la IA

- Reprodujo el fallo real: corrió `superset/sync_semantic_layer.py` contra el Superset/Postgres
  local (ya levantados de una sesión anterior) y confirmó que la corrida completa aborta con
  `HTTPError 500` sin llegar siquiera a `db07`/`db09` — el mismo patrón de BUG-029, disparado esta
  vez por `db01_cubo_matricula` (dataset distinto, misma causa raíz: ausencia de una vista Gold).
- Ubicó el único punto de falla real: `ensure_datasets()` en `superset/sync_semantic_layer.py`
  no tenía `try/except` alrededor del POST/PUT de cada dataset — un solo error sin capturar
  propagaba y tumbaba `main()` completo.
- Confirmó que `ensure_chart()` **ya** maneja datasets ausentes con gracia (retorna `(-1, "")` si
  el nombre no está en `datasets_by_name`), así que el único cambio necesario era que
  `ensure_datasets()` deje de propagar la excepción y en vez de eso reporte y continúe — exactamente
  lo que la propia fila de BUG-029 ya proponía en su columna de prueba de regresión.
- Envolvió el cuerpo del `for` de `ensure_datasets()` en `try/except Exception` (mismo estilo ya
  usado en `_apply_metrics_and_columns`, línea 505 del archivo, para no inventar un patrón nuevo):
  si falla, imprime el error y hace `continue` sin agregar el nombre a `datasets`.
- Escribió `tests/test_sync_resiliencia_bug029.py` (3 casos, sin red — mismo patrón de
  `tests/test_semantic_db01_db02.py` que importa el script como módulo y sustituye `_request`):
  1. un dataset roto (`db09_cubo_recomendaciones`) no aborta los posteriores — `db10_cubo_pipeline`
     sí se registra, que es el escenario exacto que describe BUG-029.
  2. un dataset sano *antes* del roto (`db07_*`) no se ve afectado.
  3. guarda de no-regresión: sin fallos, se registran los 16 `.sql` de siempre.
- Actualizó `Bug_Register.md`: BUG-029 pasa de `open` a `fixed`, con el fix y la prueba de
  regresión real enlazados.

## Qué revisé yo

- Verifiqué que el cambio es mínimo y quirúrgico: un solo `try/except` en una sola función, sin
  tocar el resto del script (charts, dashboards, layout) — no reescribí nada que Manuel pudiera
  tener en progreso en otra parte del archivo.
- Corrí las 3 pruebas nuevas (en verde) y la suite completa: **781 passed, 5 skipped** (los 774
  de antes + las 3 nuevas + los que trajo el fast-forward de `main` tras el merge de PR #191/#192).
- `vault_lint.py` limpio antes y después.
- No cambié el comportamiento de ningún otro flujo del script (creación de charts, dashboards,
  métricas) — solo el punto exacto que BUG-029 documenta.

## Qué falta / bloqueos

- Ninguno de mi lado para este fix específico. Queda pendiente avisarle a Manuel (dueño original
  de la "solución de fondo" según el registro previo) que este punto puntual ya quedó cubierto,
  por si él tenía algo más amplio planeado en US-205 que valga la pena coordinar.
- Sigue sin resolver el bloqueo de fondo de Bronze (Diana, C1) para que los datasets con datos
  reales se vean en Superset — este fix solo evita que un dataset roto tumbe a los demás, no
  materializa ningún cubo Gold nuevo.

## IDs tocados

US-222, US-223, US-205, BUG-029, REQ-002
