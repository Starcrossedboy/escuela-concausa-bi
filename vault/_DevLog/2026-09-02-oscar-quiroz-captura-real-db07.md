---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión única: captura real de DB-07 tras el fix de BUG-029"
touches: ["US-222", "US-224", "BUG-029", "REQ-002"]
tags: [devlog]
---

# DevLog — 2026-09-02 — Captura real de DB-07 en el manual de usuario

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué pedí

Tras corregir BUG-029 se confirmó que DB-07 (US-222) se registra en Superset local — pedí
aprovechar eso para reemplazar el marcador `[CAPTURA PENDIENTE: DB-07]` del manual con una captura
real.

## Qué hizo la IA

- Instaló Playwright + Chromium (ya estaban de una sesión anterior), se autenticó en Superset
  local vía formulario real (`#username`/`#password`, sin hardcodear la contraseña — se lee de
  `.env` en tiempo de ejecución) y navegó a
  `http://127.0.0.1:8088/superset/dashboard/db07-calidad-cobertura/`.
- Tomó la captura completa: los 4 tiles KPI, la tabla detallada y el gráfico de barras por driver
  muestran datos reales de `gold.cubo_completitud` (72 filas, ya materializado en este ambiente).
- **El mapa (deck_polygon) no hizo autozoom a México** pese a `autozoom: true` en el YAML.
  Confirmó primero que no era un problema de datos (`gold.geo_municipio` tiene las 3 geometrías
  reales, verificado por SQL directo). Intentó 3 veces forzar el zoom por scroll — la última
  con un cálculo geográfico explícito (proyección Mercator para ubicar CDMX) terminó centrada en
  Quebec, Canadá, por un error de referencia en las coordenadas del cálculo. Después de 4
  intentos sin converger, se detuvo y usó la vista sin forzar, documentando el detalle en vez de
  seguir iterando a ciegas sobre un canvas WebGL.
- Guardó la imagen en `vault/04_UX_Design/capturas/db07-calidad-cobertura.png` (324 KB, dentro del
  límite de 5 MB) y la insertó en la sección de DB-07 del manual, con una nota honesta sobre el
  mapa. Actualizó también la tabla de estado, la nota de estado de DB-07 y el conteo de marcadores
  pendientes (10 → 9).
- **Incidente y corrección:** al terminar, corrió `docker compose down` para limpiar, sin notar
  que eso apaga TODOS los contenedores del proyecto — incluidos `faro-api`, `faro-airflow-*`,
  `faro-mlflow` y `faro-chromadb`, que ya llevaban 7 días corriendo **antes** de esta sesión y no
  los había levantado esta IA. Lo detectó de inmediato (`docker ps -a` vacío), confirmó que los
  volúmenes con los datos seguían intactos (`down` sin `-v` no los toca), avisó al usuario con el
  diagnóstico completo, y tras su confirmación corrió `docker compose up -d` para restaurar los 7
  servicios al estado previo.

## Qué revisé yo

- Verifiqué con SQL directo que las geometrías de los municipios existen antes de asumir que el
  mapa vacío era un bug de datos.
- No dejé pasar el `docker compose down` sin reportarlo — aunque fue mi error, se detectó y
  corrigió en el mismo turno, con los volúmenes intactos como evidencia de que no hubo pérdida de
  datos.
- Confirmé el tamaño de la imagen (324 KB) contra la regla de 5 MB del proyecto antes de
  commitear.
- Corrí `vault_lint.py` (limpio) y la suite completa (781 passed) después de los cambios al
  manual.

## Qué falta / bloqueos

- El zoom del mapa de DB-07 sigue sin ajustar automáticamente — no bloquea nada, es un detalle de
  interacción de Superset, documentado en el propio manual para quien tome capturas de los otros
  9 dashboards.
- Los 9 marcadores `[CAPTURA PENDIENTE]` restantes siguen bloqueados por Bronze (Diana Álvarez,
  C1) — sin cambio respecto a antes.

## IDs tocados

US-222, US-224, BUG-029, REQ-002
