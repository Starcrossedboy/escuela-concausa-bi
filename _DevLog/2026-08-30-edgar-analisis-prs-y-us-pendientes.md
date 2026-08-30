---
project: "FARO"
date: "2026-08-30"
author_human: "Edgar Edmundo Coronel Navarrete"
agent: "Claude Code"
model: "Sonnet 5"
session_duration: "media — análisis de 7 PRs abiertos, simulación de orden de merge y reporte de US pendientes"
touches: ["US-004", "US-206", "US-312", "US-422", "US-522b", "US-524a", "BUG-008", "BUG-020", "ADR-007", "RPT-US-PENDIENTES-2026-08-30"]
tags: [devlog, pm, prs, status, validation]
---

# DevLog — 2026-08-30 — Análisis de PRs abiertos y reporte de US pendientes

→ [[_DevLog/_index|Volver al índice]] · [[13_Reports/US_Pendientes_Cierre_2026-08-30]] ·
[[13_Reports/Junta_Mock_2026-08-29]]

## Qué se hizo

Tres PRs nuevos aparecieron durante la noche (#135, #136, #137) y dos que estaban trabados se
destrabaron solos (#87 y #102 pasaron a mergeables). Se analizó el conjunto y se simuló el orden de
merge antes de tocar nada.

## El hallazgo del día: los cinco entran sin conflicto

Simulé la integración secuencial de #135 → #136 → #134 → #137 → #102 sobre `main`:

```
#135 ✅  #136 ✅  #134 ✅  #137 ✅  #102 ✅
630 passed, 5 skipped
```

**Cero conflictos.** Es la primera vez en dos días que ocurre, y no es casualidad: los conflictos
anteriores venían de ramas que llevaban días sin actualizarse. Estos cinco se abrieron o rebasaron
hoy.

Mi propia rama entra limpia al final. Vault limpio.

## Manuel resolvió el choque de DB-05 y eligió la opción difícil

El PR #134 chocaba con el tablero de Monserrat: el repunteo de US-205 sacaba `valor_promedio_driver`
del catálogo y los 18 charts de DB-05 la usaban. Manuel tomó la **opción B** — quitó la métrica del
catálogo **y** repunteó los charts — en vez de la salida cómoda de conservar la métrica vieja junto a
la nueva.

Verificado: `metrics_db05_db08.yaml` y `db05_analisis_driver.yaml` quedan ambos en 0 referencias, y
`test_semantic_db05_db08` pasa 53/53 con `main` mergeado. La convención queda limpia para los 10
tableros en vez de arrastrar una métrica duplicada.

## Eloisa aplicó las tres correcciones

El PR #137 llegó con el reencuadre completo: ya no dice «detecté BUG-008» sino que **BUG-008 no tenía
prueba automatizada de regresión** — su único test registrado era un `curl` manual contra producción.
Y las rutas se obtienen del esquema OpenAPI en vivo, no escritas a mano, así que la prueba no
generará falsos positivos cuando se agregue una ruta legítima.

Vale registrarlo porque es la segunda vez que su trabajo cae sobre algo ya resuelto, y las dos veces
el problema fue de planeación mía. Aquí el trabajo se convirtió en la guarda que faltaba.

## US-522b: el CI ahora sí reprueba la colisión

El PR #87 pasó a mergeable pero sus tres checks están en rojo, y uno dice exactamente:

```
❌ IDs duplicados (1): ADR-007
```

Es la confirmación de la corrección que hice ayer a V-02 del plan del vault: **el linter siempre
funcionó**; lo que fallaba era que su último check había corrido el 26-ago, antes de que existiera el
ADR-007 de Héctor. Al actualizar la rama, el check volvió a correr contra el repositorio real y
atrapó la colisión de inmediato.

Es un buen argumento para la regla que propuse: un PR con checks de más de 24 horas no se mergea sin
revalidar.

## Reporte de US pendientes

Nuevo: [[13_Reports/US_Pendientes_Cierre_2026-08-30]]. Separa las 30 historias abiertas en cuatro
grupos según **quién** las destraba, no según su estado. El dato que importa: **el 30 % se destraba
con dos decisiones** —BUG-020 y ADR-007— y no con más código.

Tres historias están abiertas por razones que sus dueños no controlan (US-412, US-524a, US-113) y lo
dejé escrito explícitamente para que no se lea como retraso personal en la revisión.

## Uso de IA

Claude Code hizo el análisis de los 7 PRs, la simulación del orden de merge, la verificación del
choque de DB-05 y la redacción del reporte. Revisé la simulación corriendo la suite completa antes de
recomendar el orden. No se pegaron datos reales ni credenciales.

## Pendiente

- Aprobar en orden: #135, #136, #134, #137, #102 y la rama del PM.
- #87 depende de que Edgar Ulises renombre su ADR a ADR-008.
- #130 se cierra: quedó redundante.
- Las tres decisiones de la junta siguen abiertas.
