---
id: ADR-006
title: "ADR-006 — Interpolación IDW de D5/D6 (agua/aire) hacia cada escuela"
owner: "Diana Aracely Alvarez Varela"
status: accepted
traces_up: ["REQ-001"]
supersedes: []
tags: [architecture, adr, gold, silver, driver-d5, driver-d6, idw, us-105]
date: "2026-08-19"
---

# ADR-006 — Interpolación IDW de D5/D6 (agua/aire) hacia cada escuela

→ [[03_Architecture/ADRs/_index|Volver a ADRs]] · [[03_Architecture/Data_Model|Data_Model §3/§7]]

## Contexto

`Data_Model.md` §3 documenta que D5 (agua, CONAGUA/DS-06) y D6 (aire, SINAICA/DS-05) son fuentes
de **estaciones/regiones puntuales** (lat/lon), sin CCT ni clave INEGI de municipio directa. La
regla del proyecto exige que, donde una fuente no cubre una escuela, el valor se marque
`SIN_DATO` explícito — nunca cero, nunca nulo silencioso — y que la interpolación se haga por
**IDW dentro de un radio válido**, registrando un índice de confianza. Hasta hoy (US-103/US-104),
D5 y D6 vivían en `SIN_DATO` explícito como placeholder honesto: el join espacial no existía
todavía. Esta ADR es el diseño de ese join, alcance de US-105.

Dos preguntas quedaban abiertas y sin documentar formalmente:
1. ¿A qué grano interpolamos — por escuela o por municipio? El seed `dim_driver.csv` (US-103,
   ya en `main`) había declarado `nivel_geografico = municipio` para D5/D6, posiblemente escrito
   antes de que `silver.escuela`/`dim_escuela` tuvieran lat/lon real por CCT.
2. ¿Qué radio de validez, qué fórmula de ponderación y qué fórmula de confianza usamos? Ninguno
   de los tres estaba especificado en ningún documento del proyecto.

## Decisión

**Interpolación IDW por escuela** (no por municipio), potencia 2 (IDW estándar), con estas
reglas concretas:

- **Grano:** un valor por `cct` (escuela), usando el lat/lon real de `dim_escuela`/`silver.escuela`
  — no un centroide de municipio inventado.
- **Radio válido:** 15 km. Fuera de radio → `SIN_DATO` explícito (nunca cero).
- **Ponderación:** IDW clásico — `valor = Σ(valor_estación / distancia²) / Σ(1/distancia²)`,
  sobre todas las estaciones dentro del radio (no solo la más cercana).
- **Índice de confianza:** `1 - (distancia_a_la_estación_más_cercana / radio_válido)` — 1.0 si la
  escuela está justo sobre una estación, 0.0 en el borde del radio.
- **D6 (aire):** usa `PM2.5` como proxy de calidad del aire — el contaminante criterio más
  reportado por SINAICA (ver `14_Data_Sources/DS-05_SINAICA_Calidad_Aire.md` §5, prueba de
  descarga real). Solo lecturas marcadas válidas por la propia API SINAICA (bandera `val = 1`).
- **D5 (agua):** mismo método, pero **todavía no implementado** — DS-06 (dueño Emilio Galnares
  Ruiz) no ha completado su "prueba de descarga real"; no hay `bronze.conagua` con datos. D5
  sigue en `SIN_DATO` explícito hasta que DS-06 entregue esquema y datos reales.
- **Distancia:** fórmula de Haversine (esfera, radio 6371 km), calculada en SQL dentro del CTE
  de Gold (`fact_escuela_ciclo.sql`/`features_escuela.sql`), no en un modelo Silver intermedio —
  mismo patrón que D1/D2 (CTEs de normalización dentro del modelo Gold, sobre tablas Silver ya
  conformadas).
- **`dim_driver.csv`** se actualiza: `nivel_geografico` de D5/D6 pasa de `municipio` a `escuela`.

## Alternativas consideradas

| Opción | Pros | Contras |
|---|---|---|
| **Por escuela (elegida)** | Más preciso; usa lat/lon real de ambos lados (estación y escuela) sin inventar nada; coherente con D3/D4 (también por cct) | Requiere que la escuela tenga lat/lon real (las que no, caen a `SIN_DATO`, igual que D1 cuando falta CONEVAL) |
| Por municipio | Reutiliza el mismo valor para todas las escuelas de un municipio, menos cómputo | `dim_municipio` no tiene lat/lon — habría que inventar un centroide (¿geométrico? ¿poblacional? ¿promedio de escuelas?) sin fuente real que lo respalde; pierde precisión en municipios grandes (ej. Iztapalapa) con variación real de calidad del aire dentro del mismo municipio |
| Solo estación más cercana (sin ponderar) | Más simple de explicar | Ignora información real de estaciones cercanas adicionales dentro del radio; menos robusto si la estación más cercana tiene una lectura atípica |
| Radio 25 km / 10 km | Más/menos escuelas con dato | 25 km reduce la confiabilidad de la lectura en el borde; 10 km deja demasiadas escuelas en `SIN_DATO` dado que SINAICA cubre solo ~80 zonas urbanas (ver DS-05.md) — 15 km es el punto medio razonable |

## Consecuencias

- **Positivas:** D6 deja de estar en `SIN_DATO` universal — las escuelas cercanas a una estación
  SINAICA activa (con lectura de PM2.5 válida) obtienen un valor real, normalizado 0-1 igual que
  el resto de los drivers. El patrón es reutilizable para D5 en cuanto DS-06 entregue datos reales
  (mismo radio, misma fórmula, mismo `dato_valido`/bandera de calidad si CONAGUA la trae).
- **Negativas / pendientes:**
  - El índice de confianza de la interpolación (`1 - distancia/radio`) se calcula pero **no se
    expone todavía como columna nueva** en `fact_escuela_ciclo`/`features_escuela` — son tablas
    de contrato compartido (`features_escuela` con Andrés González Habib/C3); agregar una columna
    ahí requiere avisar antes, no se decidió unilateralmente en esta sesión. Queda como
    **pendiente explícito**: decidir si se agrega como `d6_indice_confianza` (y su análogo para
    D5) o si se documenta solo como artefacto interno de la interpolación.
  - Sigue habiendo escuelas sin lat/lon en `dim_escuela` (los casos `SIN_DATO` ya conocidos de
    US-103) — esas también caen a `SIN_DATO` en D6, correctamente, no es un caso nuevo.

## Trazabilidad

- Requisito(s): REQ-001 (AC-001.6, cobertura parcial con `SIN_DATO` explícito)
- Historia: US-105
- Impacta: [[03_Architecture/Data_Model]] §3/§7 · `dbt/models/gold/fact_escuela_ciclo.sql` ·
  `dbt/models/gold/features_escuela.sql` · `dbt/seeds/dim_driver.csv`
- Relacionado: [[03_Architecture/ADRs/ADR-005-dim-driver-mapeo|ADR-005]] (mismo patrón de mapeo
  driver→fuente, para D3/D4)