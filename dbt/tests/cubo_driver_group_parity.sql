-- El denominador de recomendaciones coincide con el runtime por grupo.
with esperado as (
    select
        f.cve_mun,
        e.nivel,
        f.id_ciclo,
        count(distinct f.cct) as total_escuelas,
        count(r.cct) as escuelas_con_recomendacion
    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    left join {{ source('gold_ml_runtime', 'recomendaciones') }} r
        on f.cct = r.cct
        and f.id_ciclo = r.id_ciclo
    group by f.cve_mun, e.nivel, f.id_ciclo
),
cubo as (
    select
        cve_mun,
        nivel,
        id_ciclo,
        min(total_escuelas) as total_escuelas,
        max(total_escuelas) as total_escuelas_max,
        min(escuelas_con_recomendacion) as escuelas_con_recomendacion,
        max(escuelas_con_recomendacion) as escuelas_con_recomendacion_max
    from {{ ref('cubo_driver') }}
    group by cve_mun, nivel, id_ciclo
)
select
    e.cve_mun,
    e.nivel,
    e.id_ciclo
from esperado e
left join cubo c
    on e.cve_mun = c.cve_mun
    and e.nivel = c.nivel
    and e.id_ciclo = c.id_ciclo
where c.cve_mun is null
   or c.total_escuelas <> e.total_escuelas
   or c.total_escuelas_max <> e.total_escuelas
   or c.escuelas_con_recomendacion <> e.escuelas_con_recomendacion
   or c.escuelas_con_recomendacion_max <> e.escuelas_con_recomendacion
