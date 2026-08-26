-- Cada escuela/ciclo del hecho Gold debe aparecer exactamente con 6 drivers.
with conteo_cubo as (
    select
        cct,
        id_ciclo,
        count(*) as drivers
    from {{ ref('cubo_pivot') }}
    group by cct, id_ciclo
)
select
    f.cct,
    f.id_ciclo,
    coalesce(c.drivers, 0) as drivers
from {{ ref('fact_escuela_ciclo') }} f
left join conteo_cubo c
    on f.cct = c.cct
    and f.id_ciclo = c.id_ciclo
where coalesce(c.drivers, 0) <> 6
