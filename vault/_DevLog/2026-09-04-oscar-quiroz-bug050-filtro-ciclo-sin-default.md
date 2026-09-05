---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión: diagnóstico y fix de BUG-050 (filtro de ciclo sin default)"
touches: ["US-203", "US-204", "US-211a", "US-211b", "US-222", "REQ-002", "BUG-050"]
tags: [devlog]
---

# DevLog — 2026-09-04 — BUG-050: el filtro de Ciclo escolar triplicaba totales en 8/10 tableros

→ [[vault/_DevLog/_index|Volver al índice]] · [[vault/06_Quality_Testing/Bug_Register]]

## Qué pedí

Edgar reportó por Teams (mismo aviso enviado a Manuel) revisar los tiles de "total" que sumen
matrícula o escuelas en mis tableros y confirmar si respetan el filtro de ciclo vigente, por el
mismo patrón que Karla encontró en la API (BUG-044). Pedí verificar contra datos reales, no solo
contra el YAML, antes de tocar nada. Cuando Manuel afirmó dos veces por Teams que ya lo había
corregido, pedí verificarlo también contra el repo antes de darlo por cerrado. Al confirmar que
ninguna de las dos afirmaciones tenía evidencia real, pedí explicar el alcance del defecto en
términos simples y, ya con eso claro, autoricé aplicar el fix completo (código compartido +
verificación en los 8 tableros afectados, no solo el mío), con la condición de documentar
evidencia antes/después y flaggear explícitamente cualquier archivo fuera de mi propiedad directa.

## Qué hizo la IA

- Confirmó en vivo que DB-07 tenía el defecto: `total_escuelas` mostraba 25,578 (suma de los 3
  ciclos materializados) en vez de 8,382 (ciclo 2024-2025), consultando Postgres y la metadata
  real de Superset (`defaultDataMask: None` en el filtro "Ciclo escolar").
- Verificó dos veces las afirmaciones de Manuel ("ya quedó, le pusimos 2024-2025 como default") y
  ambas resultaron sin respaldo: sin commits nuevos en `dev/manuel-serrania`, sin PRs abiertos en
  el repo, sin cambio en el `defaultDataMask` real de Superset.
- Diagnosticó la causa raíz exacta: `metrics_db01_db02.yaml`, `metrics_db03_db04.yaml`,
  `metrics_db05_db08.yaml`, `metrics_db06_db09.yaml` y `metrics_db07.yaml` ya declaraban
  `default: ultimo_ciclo` en su contrato semántico, pero `_filtros_nativos()`
  (`superset/sync_semantic_layer.py`) nunca leía ese campo, y los YAML de tablero
  (`superset/dashboards/*.yaml`) tampoco lo traían — la intención estaba documentada dos veces y
  cableada cero veces.
- Corrigió `_filtros_nativos()` para resolver el valor más reciente **dinámicamente** contra los
  datos reales (`ORDER BY <columna> DESC LIMIT 1` vía `/api/v1/chart/data`), nunca hardcodeado —
  a diferencia del enfoque que describió Manuel (`"2024-2025"` fijo, que se habría quedado
  desactualizado en el próximo ciclo).
- Agregó `default: ultimo_ciclo` a los 8 YAML de tablero que ya lo declaraban en su semántica
  (`db01_ejecutivo.yaml`, `db02_mapa_riesgo.yaml`, `db03_ficha_escuela.yaml`,
  `db04_comparador_municipio.yaml`, `db05_analisis_driver.yaml`, `db06_predicciones.yaml`,
  `db07_calidad_cobertura.yaml`, `db08_explorador_cubo.yaml`, `db09_recomendaciones.yaml`) —
  permitido por `ownership.yml` (`superset/**` es alcance verde compartido por los 4 integrantes
  de Célula 2), pero fuera de mi propiedad de historia individual para 7 de los 9.
- Corrió el sync completo y verificó, dataset por dataset, el número antes/después en los 9
  datasets con métrica de conteo absoluto — tabla completa en `BUG-050`
  ([[vault/06_Quality_Testing/Bug_Register]]).
- Escribió `tests/test_filtros_nativos_default_dinamico.py` (5 casos): resolución correcta,
  ausencia de cambio cuando no hay `default:` declarado, que el valor sigue a los datos si el
  ciclo avanza (no queda fijo), que un fallo de red no rompe el sync, y una guardia paramétrica
  que recorre los 10 YAML de tablero y exige `default: ultimo_ciclo` en todo filtro `id_ciclo`
  (DB-10 exento por diseño, sin dimensión de ciclo).
- Retomó la captura real de DB-07 en `Manual_Usuario_Dashboards.md` (v1.3) con el fix aplicado y
  visible: el filtro arranca en "2024-2025" (una sola opción, no "3 options"), "Total de escuelas"
  = 8,382.

## Qué revisé yo

- No acepté la afirmación de Manuel dos veces seguidas sin evidencia — verifiqué contra `git
  fetch`, diff de ramas, lista de PRs abiertos vía API de GitHub, y la metadata real de Superset
  en ambas ocasiones.
- Antes de tocar `_filtros_nativos()`, confirmé el detalle técnico exacto (`defaultDataMask: None`
  en vivo) en vez de asumir la causa por el nombre del bug.
- Diseñé la resolución del default para que sea dinámica y no hardcodeada, evitando el defecto de
  diseño que Manuel describió (un ciclo fijo en texto que se desactualiza solo).
- Verifiqué el resultado en los 9 datasets afectados con consultas reales, no solo confié en que
  el sync terminara sin errores.
- Corrí la suite completa (872 passed) y `vault_lint` antes de dar el fix por terminado.

## Qué falta / bloqueos

- **De mi lado, ninguno.** El fix está aplicado, verificado y con pruebas de regresión.
- **Pendiente de Manuel, Marina y Monserrat:** verificar y recapturar la evidencia visual de sus
  propias historias (DB-01/02/06/09, DB-03/04, DB-05/08 respectivamente) — los números de sus
  tableros cambiaron con este fix y sus propias capturas de DoF pueden quedar desactualizadas,
  igual que la mía lo estaba.
- Se registra explícitamente en el PR que toqué archivos fuera de mi historia individual
  (permitido por ownership.yml, pero flaggeado para que ellos lo revisen antes del demo).

## IDs tocados

US-203, US-204, US-211a, US-211b, US-222, REQ-002, BUG-050
