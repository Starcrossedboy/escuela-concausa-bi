---
id: RPT-US-PENDIENTES-2026-08-30
title: "Qué le falta a cada US para cerrarse — corte del 30 de agosto de 2026"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: false
traces_up:
  - "12_Roadmap_Sprints/Execution_Status"
  - "06_Quality_Testing/Bug_Register"
traces_down:
  - "13_Reports/Junta_Mock_2026-08-29"
last_reviewed: "2026-08-30"
tags: [report, validation, user-stories, follow-up, pm]
---

# Qué le falta a cada US para cerrarse — 30 de agosto de 2026

> **30 historias sin cerrar.** Este documento separa las que dependen de su dueño de las que están
> frenadas por algo ajeno, porque la conversación es distinta en cada caso: a unas se les pide
> trabajo, a otras se les quita un obstáculo.
> → [[12_Roadmap_Sprints/Execution_Status]] · [[13_Reports/Junta_Mock_2026-08-29]]

## Resumen

| Categoría | US | Quién destraba |
|---|---|---|
| **A · Bloqueadas por BUG-020** | 5 | Christian Ruiz + Luis Téllez |
| **B · Bloqueadas por ADR-007** | 4 | La mesa de ratificación |
| **C · Bloqueadas por otra persona** | 6 | Un tercero, no su dueño |
| **D · Dependen de su dueño** | 15 | Su dueño |

**El 30 % de lo que falta se destraba con dos decisiones**, no con más código.

---

## A · Bloqueadas por BUG-020 — la URL pública responde 500

**Ninguna de estas cinco puede cerrarse hoy aunque su código esté perfecto**, por el criterio del
28-ago: una historia cuyo entregable es una ruta HTTP de la API no cierra si esa ruta no responde en
el despliegue que se va a demostrar.

| US | Dueño | Estado del código | Qué falta |
|---|---|---|---|
| `US-411` | Karla Monter | ✅ Endpoints sobre Gold real | Que la ruta responda en producción · ratificar `/series` fuera de alcance |
| `US-412` | Juan Carlos Macías | ✅ Código y pruebas correctos | **Reabierta por este criterio.** Sólo espera el 500 |
| `US-403` | Christian Ruiz | ✅ RBAC ciudadano/analista | Definir `ANALISTA_EMAILS` · E2E 401/403 sobre la URL pública |
| `US-305` | Andrés González | ✅ Widget, historial y JWT | E2E widget→API→RAG con login real |
| `US-304a` | Andrés González | ✅ Guardarraíles reales | **BUG-025**: el endpoint desplegado sigue siendo el stub |

> **Nota para la junta:** US-412 es el caso más incómodo — el trabajo está bien hecho y la historia
> está abierta por una razón que su dueño no controla. Vale reconocerlo explícitamente para que no se
> lea como retraso suyo.

---

## B · Bloqueadas por ADR-007 — decisión, no código

**Se cierran o avanzan el mismo día que se ratifique la unidad de `target_variacion_matricula`.**

| US | Dueño | Qué falta |
|---|---|---|
| `US-212` | Marina García | **Al 95 %.** Sólo verificar los bloques de predicción de DB-03 (AC-002.4), que dependen de la unidad. Si se ratifica fracción, su umbral 0.6 sigue válido y no toca nada |
| `US-313` | Héctor Morales | Publicación batch a Gold: la guarda de BUG-017 detiene la publicación mientras la unidad esté sin decidir |
| `US-311` | Héctor Morales | ML-01 entrena, pero el `indice_riesgo` publicado depende de la calibración |
| `US-104` | Diana Alvarez | `features_escuela.sql` produce alumnos absolutos; cambia sólo si se ratifica fracción |

**Coste de no decidir:** medio sprint de Célula 2 y `DB-04` mostrando «100 % de escuelas en riesgo»,
un número creíble que está mal.

---

## C · Bloqueadas por un tercero

| US | Dueño | Espera a | Qué falta exactamente |
|---|---|---|---|
| `US-113` | Deni Garrido | **Nadie — ya se destrabó** | DS-06 entró con el PR #107 y su extractor es un `POST` automatizado, no descarga manual. Con BUG-026 cerrado el pipeline es reproducible desde fixtures. **Materializar DB-10 `cubo_pipeline`, validarlo y confirmar el cierre** |
| `US-524a` | Alejandro Velázquez | **Luis Téllez** | Todo resuelto. Falta el Approve de C5 por regla 7 (toca el CMD del contenedor). Pedido hace días |
| `US-522b` | Edgar Ulises Jiménez | **Él mismo** | Conflictos ya resueltos por el PM. Falta renombrar su ADR a **ADR-008** —hoy colisiona con el de Héctor y el CI lo reprueba— y marcar las casillas del PR |
| `US-222` | Oscar Quiroz | **Su decisión** | Capa de datos lista y validada. Falta cargar `superset/mock/gold_ml_outputs_mock.sql` —Manuel ya lo autorizó— y construir el tablero visual. También dar de alta **BUG-029** |
| `US-204` | Manuel Serranía | **Héctor Morales** | Repetir 15/15 charts con salidas reales de US-313, que a su vez espera ADR-007 |
| `US-324` | Carlos Mayorga | **Los 3 dueños de modelo** | Corregir la ficha ML-03 —ya no es cierto que esté sin implementar— y obtener revisión de Héctor, Andrés y Estefany |

---

## D · Dependen de su dueño

| US | Dueño | Qué falta para cerrarla |
|---|---|---|
| `US-106` | Diana Alvarez | Trabajo pendiente de su plan |
| `US-206` | Manuel Serranía | Repunteo de la capa semántica — **PR #134, listo para aprobar** |
| `US-207` | Marina García | Pendiente de arranque |
| `US-302` | Andrés González | Gold real, Registry en Docker, endpoint SHAP y pasar el documento a `approved` |
| `US-303` | Andrés González | E2E contra MLflow real y verificación conjunta ML-01/02/03. La exposición vía API depende de BUG-020 |
| `US-304b` | Carlos Mayorga | Probar la recuperación RAG dentro del contenedor |
| `US-312` | Héctor Morales | **PR #135 lo cierra**: ML-03 entra a la evaluación y cubre AC-003.2 |
| `US-404` `US-405` | Christian Ruiz | Pendientes de arranque |
| `US-416` | Juan Carlos Macías | Ratificar el diseño y que el E2E de Postgres pertenece a US-422 |
| `US-422` | Eloisa González | **Arrancó con el PR #137.** Quedan las 18 rutas del contrato por cubrir |
| `US-504` `US-505` | Luis Téllez | Pendientes de arranque |
| `US-521b` | Edgar Ulises Jiménez | Guía de ambiente local |
| `US-521c` | Edward Ruiz | Convertir el DevLog a `.md` filed, actualizar índice y repetir la guía |
| `US-522a` | Alejandro Velázquez | E2E local Compose API↔Postgres |
| `US-522c` | Edward Ruiz | Verificar conexión, escribir DevLog y pasar BUG-004 a `fixed` |
| `US-004` | Edgar Coronel | Historia continua hasta el cierre del proyecto |

---

## Lo que hay que decir en voz alta

**Tres historias están abiertas por razones que sus dueños no controlan** y conviene reconocerlo para
que no se lea como retraso personal:

- **US-412** (Juan Carlos) — código y pruebas correctos, abierta sólo por BUG-020.
- **US-524a** (Alejandro) — resolvió todo lo que se le pidió; espera una firma.
- **US-113** (Deni) — su bloqueo desapareció hace horas y probablemente aún no lo sabe.

**Y una que sí requiere insistencia:** `US-522b` lleva desde el 25-ago abierta y el CI la reprueba por
una colisión de ID que se corrige renombrando un archivo.

## Riesgo que no aparece en ninguna fila

**`DS-07` (CONEVAL) sigue en `status: draft`** con la prueba de descarga marcada como pendiente desde
la Semana 1. Alimenta **D1, pobreza y rezago social** — el primer driver y uno de los dos con
cobertura nacional. No bloquea ninguna US formalmente, y por eso nadie lo está mirando; pero sin dato
real, la recomendación prescriptiva pierde la dimensión de mayor peso en el target.
