{{ config(materialized='materialized_view') }}

-- US-113 / DB-08
-- Grano canónico: cct × id_driver × id_ciclo.
-- `nivel` viaja como atributo para el filtro global.
-- Los 6 drivers se convierten de ancho a largo sin transformar SIN_DATO en 0.
-- Salidas ML se unen por cct × id_ciclo para que el explorador pueda cruzarlas.
-- Cobertura explícita:
--   cobertura_driver        = bandera original D1..D6
--   cobertura_prediccion    = OK / SIN_DATO
--   cobertura_recomendacion = OK / SIN_DATO

with base as (
    select
        f.cct,
        f.id_ciclo,
        f.cve_mun,
        f.matricula_total,
        f.variacion_matricula,
        f.indice_completitud_drivers,

        e.nombre as nombre_escuela,
        e.nivel,
        e.sostenimiento,
        e.cve_ent,

        dm.nombre_municipio,
        dm.nombre_entidad,

        dt.ciclo,
        dt.anio_inicio,

        f.d1, f.d1_cobertura,
        f.d2, f.d2_cobertura,
        f.d3, f.d3_cobertura,
        f.d4, f.d4_cobertura,
        f.d5, f.d5_cobertura,
        f.d6, f.d6_cobertura

    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    inner join {{ ref('dim_municipio') }} dm
        on f.cve_mun = dm.cve_mun
    inner join {{ ref('dim_tiempo') }} dt
        on f.id_ciclo = dt.id_ciclo
),

driver_largo as (
    select
        b.*,
        v.id_driver,
        v.valor_driver,
        v.cobertura_driver
    from base b
    cross join lateral (
        values
            ('D1', b.d1, b.d1_cobertura),
            ('D2', b.d2, b.d2_cobertura),
            ('D3', b.d3, b.d3_cobertura),
            ('D4', b.d4, b.d4_cobertura),
            ('D5', b.d5, b.d5_cobertura),
            ('D6', b.d6, b.d6_cobertura)
    ) v(id_driver, valor_driver, cobertura_driver)
),

pred_ml01 as (
    select
        p.cct,
        p.id_ciclo,
        p.valor as variacion_proyectada,
        p.indice_riesgo,
        p.probabilidad
    from {{ source('gold_ml_runtime', 'predicciones') }} p
    where p.modelo = 'ML-01'
      and coalesce(nullif(to_jsonb(p)->>'grano', ''), 'escuela') = 'escuela'
)

select
    d.cct,
    d.id_driver,
    d.id_ciclo,

    d.ciclo,
    d.anio_inicio,

    d.nombre_escuela,
    d.nivel,
    d.sostenimiento,
    d.cve_ent,
    d.cve_mun,
    d.nombre_municipio,
    d.nombre_entidad,

    dd.nombre as nombre_driver,

    d.valor_driver,
    d.cobertura_driver,

    d.matricula_total,
    d.variacion_matricula,
    d.indice_completitud_drivers,

    p.variacion_proyectada,
    p.indice_riesgo,
    p.probabilidad,

    r.driver_dominante,
    r.recomendacion,
    r.prioridad,

    case
        when p.cct is null then 'SIN_DATO'
        else 'OK'
    end as cobertura_prediccion,

    case
        when r.cct is null then 'SIN_DATO'
        else 'OK'
    end as cobertura_recomendacion

from driver_largo d
inner join {{ ref('dim_driver') }} dd
    on d.id_driver = dd.id_driver
left join pred_ml01 p
    on d.cct = p.cct
    and d.id_ciclo = p.id_ciclo
left join {{ source('gold_ml_runtime', 'recomendaciones') }} r
    on d.cct = r.cct
    and d.id_ciclo = r.id_ciclo
