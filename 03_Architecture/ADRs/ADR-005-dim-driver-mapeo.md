---
id: ADR-005
title: "ADR-005 — Mapeo de D3/D4 en dim_driver: infraestructura y conectividad desde CEMABE"
owner: "Diana Aracely Alvarez Varela"
status: accepted
traces_up: ["REQ-001"]
supersedes: []
tags: [architecture, adr, gold, dim_driver]
date: "2026-08-17"
---

# ADR-005 — Mapeo de D3/D4 en dim_driver: infraestructura y conectividad desde CEMABE

## Contexto
`03_Architecture/Data_Model.md` §4.2 y la tabla de `14_Data_Sources/_index.md` documentan que `dim_driver` tiene 6 filas (`D1`...`D6`) y que **CEMABE (DS-03)** alimenta dos de ellas — `D3` y `D4` — pero ningún documento especifica cuál corresponde a cuál. `src/modelos/riesgo.py` (donde eventualmente se define el enum `driver_dominante`) todavía no existe.

## Decisión
Se asigna:
- **D3 = infraestructura** — columnas CEMABE de `drenaje`, `electricidad`, `sanitarios`.
- **D4 = conectividad** — columnas CEMABE de `internet`, `computadoras`.

`agua` (columna CEMABE a nivel escuela) no determina D3/D4; el driver de agua (`D5`) se alimenta de CONAGUA SINA (DS-06) a nivel municipal, una fuente y granularidad distintas.

## Alternativas consideradas
| Opción | Pros | Contras |
|---|---|---|
| D3=infraestructura, D4=conectividad | Separa limpiamente "instalaciones físicas" de "acceso digital"; alinea con los 6 factores de negocio del proyecto | Ninguno relevante |
| D3=conectividad, D4=infraestructura | Igual de válida sin más contexto | Orden arbitrario, sin justificación adicional |

## Consecuencias
- Positivas: desbloquea el seed `dim_driver.csv` de US-103 y da a Célula 3 un mapeo explícito para cuando construyan `src/modelos/riesgo.py`.
- Negativas / trade-offs: si Célula 3 ya tenía un supuesto distinto, esta ADR debe revisarse con ellos antes del code freeze.

## Trazabilidad
- Requisito: REQ-001 · Impacta: [[03_Architecture/Data_Model]] §4.2, `dbt/seeds/dim_driver.csv`