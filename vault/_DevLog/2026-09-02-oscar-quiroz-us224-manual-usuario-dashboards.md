---
author_human: "Oscar Antonio Quiroz Lázaro"
agent: "Claude Code"
model: "claude-sonnet-5"
session_duration: "sesión única: US-224 manual de usuario de dashboards"
touches: ["US-224", "REQ-002", "DOC-MANUAL-DASHBOARDS"]
tags: [devlog]
---

# DevLog — 2026-09-02 — US-224: Manual de usuario de dashboards

→ [[vault/_DevLog/_index|Volver al índice]]

## Qué pedí

Construir el entregable de US-224: una guía con capturas de los 10 dashboards para el pitch de
entrega y el README, en lenguaje de negocio (no la especificación técnica que ya cubre
[[vault/04_UX_Design/Screen_Specs]]).

## Qué hizo la IA

- Redactó [[vault/04_UX_Design/Manual_Usuario_Dashboards]]: propósito por dashboard, cómo leerlo,
  mapa de navegación (mermaid + tabla de drill-down), filtros globales, y una narrativa sugerida
  de 5 pasos para la demo en vivo — usando [[vault/04_UX_Design/Screen_Specs]] como fuente de
  verdad para no inventar KPIs ni cubos.
- Antes de escribir, intentó conseguir capturas reales:
  1. Levantó Docker Desktop y `docker compose up -d db superset`; Superset quedó sano.
  2. Instaló Playwright (Python + Chromium) para poder navegar y capturar pantallas.
  3. Encontró que el Postgres local no tiene Bronze cargado (mismo bloqueo que
     [[vault/04_UX_Design/Cube_Specs_DB07]]/[[vault/04_UX_Design/Cube_Specs_DB10]] ya documentan):
     solo 12 filas en `fact_escuela_ciclo`, 3 municipios.
  4. Cargó los mocks ya sancionados por el equipo (`superset/mock/gold_estrella_mock.sql` y
     `gold_ml_outputs_mock.sql`, mismo patrón usado por Manuel/Marina en US-203/US-212) — no
     insertaron filas nuevas porque ya existía un mock previo, con esquema **anterior a BUG-031**
     (le faltaba `matricula_ciclo_anterior`).
  5. Corrigió el esquema local (`ALTER TABLE` + backfill) — dato sintético, sin tocar ningún
     archivo del repo ni datos de otras personas.
  6. Intentó `dbt run --select cubo_matricula cubo_riesgo_territorial` para materializar los cubos
     que Superset necesita — el clasificador de modo automático bloqueó el comando.
- Se detuvo y le explicó la situación al usuario en vez de intentar evadir el bloqueo. El usuario
  decidió no seguir peleando con el ambiente (ya era tiempo considerable por un bloqueo que ni
  siquiera es de Célula 2) y optó por entregar el manual completo hoy con capturas pendientes
  marcadas, en vez de forzar 2 de 10 dashboards con datos sintéticos.
- Agregó el documento a [[vault/04_UX_Design/_index]], una sección "📊 Dashboards" en `README.md`
  con el enlace, y una fila de evidencia incremental en
  [[vault/02_Requirements/Traceability_Matrix]].

## Qué revisé yo

- Confirmé que cada afirmación del manual (KPIs, cubos, umbral de riesgo 0.6, regla `SIN_DATO`)
  viene literalmente de `Screen_Specs.md`, no inventada.
- Revisé que el `status: draft` (no `approved`) sea honesto dado que faltan las 10 capturas.
- Verifiqué que el `ALTER TABLE` sobre el Postgres local no tocó ningún archivo versionado ni datos
  de otra persona — es estado efímero de mi propio contenedor Docker.

## Qué falta / bloqueos

- **Bloqueo real, no resuelto aquí:** Bronze no está cargado en ningún ambiente local disponible
  para mí; reemplazar los 10 marcadores `[CAPTURA PENDIENTE]` requiere el ambiente con datos reales
  (o al menos los mocks + `dbt run` completo, que el clasificador bloqueó esta sesión).
- `README.md` y `vault/12_Roadmap_Sprints/Sprints/2-oscar-antonio-quiroz-lazaro.md` (para marcar
  US-224) no están en mi verde/amarillo de `ownership.yml` — el cambio de README es mínimo (una
  sección con un link) pero declarado aquí para que se revise igual.
- Pendiente actualizar la tabla de seguimiento de mi sprint plan marcando US-224 como en curso.

## IDs tocados

US-224, REQ-002, DOC-MANUAL-DASHBOARDS
