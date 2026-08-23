{{ config(materialized='materialized_view') }}

-- US-113 / DB-05
-- Grano aprobado por Diana, pendiente de publicación canónica en DEC-009:
-- id_driver × cve_mun × nivel × id_ciclo.
--
-- El universo observado se expande a los 6 drivers para distinguir:
--   * 0 real: hay recomendaciones en el grupo, pero ninguna eligió ese driver.
--   * SIN_DATO: el grupo no tiene recomendaciones ML-02; escuelas_driver queda NULL.
--
-- No se precalculan razones. Para distribución:
--   SUM(escuelas_driver) / SUM(escuelas_con_recomendacion)
-- al agrupar por id_driver.
--
-- `cobertura_fuente` es metadata del catálogo (Nacional/Regional/Parcial).
-- `cobertura_recomendacion` es la bandera analítica OK/SIN_DATO.

with grupos as (
    select
        f.cve_mun,
        dm.cve_ent,
        dm.nombre_municipio,
        dm.nombre_entidad,
        e.nivel,
        f.id_ciclo,
        dt.ciclo,
        dt.anio_inicio,
        count(distinct f.cct) as total_escuelas

    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    inner join {{ ref('dim_municipio') }} dm
        on f.cve_mun = dm.cve_mun
    inner join {{ ref('dim_tiempo') }} dt
        on f.id_ciclo = dt.id_ciclo

    group by
        f.cve_mun,
        dm.cve_ent,
        dm.nombre_municipio,
        dm.nombre_entidad,
        e.nivel,
        f.id_ciclo,
        dt.ciclo,
        dt.anio_inicio
),

recomendaciones_grupo as (
    select
        f.cve_mun,
        e.nivel,
        f.id_ciclo,
        count(*) as escuelas_con_recomendacion

    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    inner join {{ source('gold_ml_runtime', 'recomendaciones') }} r
        on f.cct = r.cct
        and f.id_ciclo = r.id_ciclo

    group by
        f.cve_mun,
        e.nivel,
        f.id_ciclo
),

recomendaciones_driver as (
    select
        f.cve_mun,
        e.nivel,
        f.id_ciclo,
        r.driver_dominante as id_driver,
        count(*) as escuelas_driver

    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    inner join {{ source('gold_ml_runtime', 'recomendaciones') }} r
        on f.cct = r.cct
        and f.id_ciclo = r.id_ciclo

    group by
        f.cve_mun,
        e.nivel,
        f.id_ciclo,
        r.driver_dominante
)

select
    d.id_driver,
    d.nombre as nombre_driver,
    d.fuente as fuente_driver,
    d.cobertura as cobertura_fuente,
    d.nivel_geografico,

    g.cve_mun,
    g.cve_ent,
    g.nombre_municipio,
    g.nombre_entidad,
    g.nivel,
    g.id_ciclo,
    g.ciclo,
    g.anio_inicio,

    g.total_escuelas,
    coalesce(rg.escuelas_con_recomendacion, 0) as escuelas_con_recomendacion,
    g.total_escuelas - coalesce(rg.escuelas_con_recomendacion, 0)
        as escuelas_sin_recomendacion,

    case
        when coalesce(rg.escuelas_con_recomendacion, 0) = 0 then null
        else coalesce(rd.escuelas_driver, 0)
    end as escuelas_driver,

    case
        when coalesce(rg.escuelas_con_recomendacion, 0) = 0 then 'SIN_DATO'
        else 'OK'
    end as cobertura_recomendacion

from grupos g
cross join {{ ref('dim_driver') }} d
left join recomendaciones_grupo rg
    on g.cve_mun = rg.cve_mun
    and g.nivel = rg.nivel
    and g.id_ciclo = rg.id_ciclo
left join recomendaciones_driver rd
    on g.cve_mun = rd.cve_mun
    and g.nivel = rd.nivel
    and g.id_ciclo = rd.id_ciclo
    and d.id_driver = rd.id_driver
