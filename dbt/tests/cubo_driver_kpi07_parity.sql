-- KPI-07: los conteos por driver coinciden exactamente con gold.recomendaciones.
with esperado as (
    select
        r.driver_dominante as id_driver,
        f.cve_mun,
        e.nivel,
        f.id_ciclo,
        count(*) as escuelas_driver
    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    inner join {{ source('gold_ml_runtime', 'recomendaciones') }} r
        on f.cct = r.cct
        and f.id_ciclo = r.id_ciclo
    group by r.driver_dominante, f.cve_mun, e.nivel, f.id_ciclo
)
select
    e.id_driver,
    e.cve_mun,
    e.nivel,
    e.id_ciclo
from esperado e
left join {{ ref('cubo_driver') }} c
    on e.id_driver = c.id_driver
    and e.cve_mun = c.cve_mun
    and e.nivel = c.nivel
    and e.id_ciclo = c.id_ciclo
where c.id_driver is null
   or c.escuelas_driver <> e.escuelas_driver
