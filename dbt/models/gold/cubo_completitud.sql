{{ config(materialized='materialized_view') }}

-- US-113 / DB-07
-- Grano aprobado: cve_mun × nivel × id_driver × id_ciclo.
-- DEC-009: conservar nivel antes de agregar y almacenar componentes aditivos.
-- Ninguna razón se precalcula: los porcentajes se calculan downstream como
-- SUM(numerador) / NULLIF(SUM(denominador), 0).
-- SIN_DATO nunca se convierte a cero.

with base as (

    select
        f.cct,
        f.cve_mun,
        dm.cve_ent,
        dm.nombre_municipio,
        dm.nombre_entidad,
        e.nivel,
        f.id_ciclo,
        dt.ciclo,
        dt.anio_inicio,
        f.indice_completitud_drivers,
        f.d1_cobertura,
        f.d2_cobertura,
        f.d3_cobertura,
        f.d4_cobertura,
        f.d5_cobertura,
        f.d6_cobertura
    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    inner join {{ ref('dim_municipio') }} dm
        on f.cve_mun = dm.cve_mun
    inner join {{ ref('dim_tiempo') }} dt
        on f.id_ciclo = dt.id_ciclo

),

drivers as (

    select
        b.*,
        d.id_driver,
        d.cobertura
    from base b
    cross join lateral (
        values
            ('D1', b.d1_cobertura),
            ('D2', b.d2_cobertura),
            ('D3', b.d3_cobertura),
            ('D4', b.d4_cobertura),
            ('D5', b.d5_cobertura),
            ('D6', b.d6_cobertura)
    ) as d(id_driver, cobertura)

)

select
    d.cve_mun,
    d.cve_ent,
    d.nombre_municipio,
    d.nombre_entidad,
    d.nivel,
    d.id_ciclo,
    d.ciclo,
    d.anio_inicio,
    d.id_driver,
    dd.nombre as nombre_driver,

    count(*)::bigint as total_escuelas,
    count(*) filter (where d.cobertura = 'OK')::bigint as escuelas_con_dato,
    count(*) filter (where d.cobertura = 'SIN_DATO')::bigint as escuelas_sin_dato,
    sum(d.indice_completitud_drivers) as suma_completitud,

    case
        when count(*) filter (where d.cobertura = 'OK') = 0 then 'SIN_DATO'
        else 'OK'
    end as cobertura_driver

from drivers d
inner join {{ ref('dim_driver') }} dd
    on d.id_driver = dd.id_driver
group by
    d.cve_mun,
    d.cve_ent,
    d.nombre_municipio,
    d.nombre_entidad,
    d.nivel,
    d.id_ciclo,
    d.ciclo,
    d.anio_inicio,
    d.id_driver,
    dd.nombre
