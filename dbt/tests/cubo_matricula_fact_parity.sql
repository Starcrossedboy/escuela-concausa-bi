-- DB-01: ningún grupo observado desaparece y sus componentes coinciden.
with esperado as (
    select
        f.cve_mun,
        e.nivel,
        f.id_ciclo,
        count(distinct f.cct) as escuelas,
        sum(f.matricula_total) as matricula_total,
        sum(f.matricula_ciclo_anterior) as suma_matricula_anterior,
        sum(f.indice_completitud_drivers) as suma_completitud
    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e on f.cct = e.cct
    group by f.cve_mun, e.nivel, f.id_ciclo
)
select
    e.cve_mun, e.nivel, e.id_ciclo
from esperado e
left join {{ ref('cubo_matricula') }} c
    on e.cve_mun = c.cve_mun
    and e.nivel = c.nivel
    and e.id_ciclo = c.id_ciclo
where c.cve_mun is null
   or c.escuelas <> e.escuelas
   or c.matricula_total <> e.matricula_total
   or abs(c.suma_matricula_anterior - e.suma_matricula_anterior) > 0.0000001
   or abs(c.suma_completitud - e.suma_completitud) > 0.0000001
