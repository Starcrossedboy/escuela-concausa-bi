---
id: DOC-US221-KPIS-BASE
title: "US-221 — Gráficos base de KPIs (series de matrícula, distribución por nivel y tarjetas reutilizables)"
owner: "Oscar Antonio Quiroz Lázaro"
status: in_review
traces_up: ["04_UX_Design/Screen_Specs", "US-201", "02_Requirements/User_Stories"]
traces_down: []
tags: [celula-2, kpis, superset, us-221]
---

# US-221 — Gráficos base de KPIs

> Implementa **US-221** (REQ-002): series de matrícula, distribución por nivel
> educativo y tarjetas de KPI reutilizables. Consume el catálogo canónico de
> [[04_UX_Design/Screen_Specs]] (US-201, Manuel Serranía) sin redefinir fórmulas.

## 1. Alcance

Este artefacto construye los componentes de KPI que Screen_Specs.md §2 exige como
"KPIs globales" en todo tablero (AC-002.5): contexto de matrícula, contexto de
riesgo y una serie de tiempo de matrícula.

| KPI | Tipo | Archivo SQL |
|---|---|---|
| KPI-01 · Matrícula total | Serie de tiempo | `sql/kpi_01_matricula_total.sql` |
| KPI-02 · Variación de matrícula (%Δ ponderado) | Tarjeta de contexto | `sql/kpi_02_variacion_matricula.sql` |
| KPI-03 · Índice de riesgo promedio | Tarjeta de contexto | `sql/kpi_03_indice_riesgo_promedio.sql` |
| KPI-04 · Escuelas en riesgo | Tarjeta de contexto | `sql/kpi_04_escuelas_en_riesgo.sql` |
| KPI-08 · Escuelas por nivel educativo | Distribución | `sql/kpi_08_escuelas_por_nivel.sql` |

Las 5 fórmulas son copia literal del catálogo canónico (`Screen_Specs.md` §4,
dueño Manuel Serranía, US-201) — este documento no las redefine.

## 2. Fuente de datos

- **Producción:** `gold.fact_escuela_ciclo` + dimensiones (`dim_tiempo`,
  `dim_escuela`, `dim_municipio`) y `gold.predicciones` (ML-01), vía Postgres.
- **Desarrollo/pruebas:** fixtures sintéticas en `fixtures/generate_fixtures.py`
  (SQLite, ≤500 filas, anonimizadas, alcance `SCOPE_ENTIDADES = ['09','15','19','14']`).
  Verificado el 2026-08-27 contra Postgres real:
  - `gold.predicciones` **no existe todavía** (ML-01 pendiente) — bloqueo real y
    confirmado para KPI-03/KPI-04, que dependen de esa tabla.
  - `gold.fact_escuela_ciclo` sí existe pero con solo 12 filas y 2/4 niveles
    educativos poblados (falta PREESCOLAR y MEDIA SUPERIOR) — insuficiente para
    un test automatizado reproducible de KPI-01/02/08, aunque no es un bloqueo
    absoluto como en el caso anterior.
- El cambio de fuente (fixtures → Gold real) no requiere tocar el SQL: mismo
  esquema de columnas y llaves (`cct`, `cve_mun`, `id_ciclo`).

## 3. Reutilización con US-203 (Manuel Serranía)

DB-01 Ejecutivo (US-203) debe mostrar estas mismas tarjetas de contexto por
Screen_Specs.md §2. El contrato de reutilización:
- Mismas fórmulas SQL, sin variaciones.
- Mismo grano y llaves de cruce (`cct`, `cve_mun`, `id_ciclo`).
- Mismos filtros globales (`id_ciclo`, `cve_ent`, `nivel`) — ver
  `superset_semantic/metrics_kpis_base_us221.yaml`.

Pendiente de confirmar con Manuel antes de cerrar: si DB-01 embebe estos
componentes tal cual o los reconstruye — ver DevLog de la sesión.

## 4. Reglas de calidad aplicadas

- **Nunca 0 por SIN_DATO** (P2, AC-002.6): KPI-03 y KPI-04 usan `JOIN` interno a
  `predicciones`, así que las escuelas sin puntuar (ML-01 llega en S4) se
  excluyen del promedio/conteo en vez de contarse como riesgo 0.
- **Umbral de riesgo ratificado** (DEC-006): KPI-04 usa `indice_riesgo >= 0.6`.
- **Alcance geográfico** (Screen_Specs.md §5): acotado a `SCOPE_ENTIDADES`
  (09 CDMX, 15 Edomex, 19 Nuevo León, 14 Jalisco).
- **Variación como razón, no porcentaje crudo:** KPI-02 se guarda como razón;
  el `%` lo aplica el formato d3 en Superset (`,.1%`), nunca `*100` en SQL.

## 5. Pruebas

`tests/test_kpis_us221.py` — 6 casos, corre contra las fixtures sintéticas:
valida que ninguna consulta devuelva 0/NULL indebido por SIN_DATO, que el
umbral de riesgo se aplique correctamente, que los 4 niveles educativos
aparezcan, y que el alcance geográfico respete `SCOPE_ENTIDADES`.

## 6. Trazabilidad

- **Implementa:** US-221 (REQ-002)
- **Consume:** [[04_UX_Design/Screen_Specs]] (catálogo canónico, US-201)
- **Alimenta (pendiente de confirmar con Manuel):** US-203 (DB-01 Ejecutivo)
