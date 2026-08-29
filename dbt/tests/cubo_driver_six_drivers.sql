-- Toda combinación observada municipio×nivel×ciclo debe tener D1..D6,
-- incluso cuando no exista ninguna recomendación.
with esperado as (
    select
        f.cve_mun,
        e.nivel,
        f.id_ciclo
    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    group by f.cve_mun, e.nivel, f.id_ciclo
),
conteos as (
    select
        cve_mun,
        nivel,
        id_ciclo,
        count(*) as filas,
        count(distinct id_driver) as drivers
    from {{ ref('cubo_driver') }}
    group by cve_mun, nivel, id_ciclo
)
select
    e.cve_mun,
    e.nivel,
    e.id_ciclo
from esperado e
left join conteos c
    on e.cve_mun = c.cve_mun
    and e.nivel = c.nivel
    and e.id_ciclo = c.id_ciclo
where coalesce(c.filas, 0) <> 6
   or coalesce(c.drivers, 0) <> 6
