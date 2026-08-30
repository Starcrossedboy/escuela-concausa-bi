-- Ningún grupo observado puede desaparecer por ausencia de ML.
with esperado as (
    select
        f.cve_mun,
        e.nivel,
        f.id_ciclo,
        count(distinct f.cct) as escuelas,
        sum(f.matricula_total) as matricula_total
    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e on f.cct = e.cct
    group by f.cve_mun, e.nivel, f.id_ciclo
)
select
    e.cve_mun, e.nivel, e.id_ciclo
from esperado e
left join {{ ref('cubo_riesgo_territorial') }} c
    on e.cve_mun = c.cve_mun
    and e.nivel = c.nivel
    and e.id_ciclo = c.id_ciclo
where c.cve_mun is null
   or c.escuelas <> e.escuelas
   or c.matricula_total <> e.matricula_total
