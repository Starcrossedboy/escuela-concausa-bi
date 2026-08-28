{{ config(materialized='materialized_view') }}

-- US-113 / DB-09
-- Grano: una fila por cct × id_ciclo del universo escolar observado.
-- Regla US-113: cada cubo expone cobertura explícita; una escuela sin
-- recomendación NO depende de Superset para inferir ausencia.
--
-- KPI-11 conserva exactamente la semántica canónica:
--   COUNT(*) FROM gold.recomendaciones
-- equivale a:
--   SUM(recomendacion_emitida) FROM gold.cubo_recomendaciones
-- porque recomendaciones tiene llave cct × id_ciclo y se valida paridad.
--
-- Ausencia = NULL + cobertura_recomendacion='SIN_DATO'; nunca 0 en campos ML.
-- El único 0 permitido es el componente aditivo `recomendacion_emitida`.

select
    f.cct,
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio,

    e.nombre as nombre_escuela,
    e.nivel,
    e.sostenimiento,
    e.cve_ent,
    f.cve_mun,
    dm.nombre_municipio,
    dm.nombre_entidad,

    f.matricula_total,
    f.indice_completitud_drivers,

    r.driver_dominante,
    dd.nombre as nombre_driver,
    r.recomendacion,
    r.prioridad,

    case
        when r.cct is null then 0
        else 1
    end::smallint as recomendacion_emitida,

    case
        when r.cct is null then 'SIN_DATO'
        else 'OK'
    end as cobertura_recomendacion

from {{ ref('fact_escuela_ciclo') }} f
inner join {{ ref('dim_escuela') }} e
    on f.cct = e.cct
inner join {{ ref('dim_tiempo') }} dt
    on f.id_ciclo = dt.id_ciclo
inner join {{ ref('dim_municipio') }} dm
    on f.cve_mun = dm.cve_mun
left join {{ source('gold_ml_runtime', 'recomendaciones') }} r
    on f.cct = r.cct
    and f.id_ciclo = r.id_ciclo
left join {{ ref('dim_driver') }} dd
    on r.driver_dominante = dd.id_driver
