-- ADR-007: gold.features_escuela debe publicar variación como fracción.
with matricula_ciclo as (
    select
        cct,
        ciclo as id_ciclo,
        alumnos_total as matricula_total,
        cast(split_part(ciclo, '-', 1) as int) as anio_inicio
    from {{ ref('matricula') }}
    where cve_ent in {{ scope_entidades() }}
),
serie as (
    select
        *,
        lag(matricula_total) over (
            partition by cct order by anio_inicio
        ) as matricula_ciclo_anterior
    from matricula_ciclo
),
esperado as (
    select
        cct,
        id_ciclo,
        cast(matricula_total as double precision)
            / cast(matricula_ciclo_anterior as double precision)
            - 1.0 as target_esperado
    from serie
    where matricula_ciclo_anterior is not null
      and matricula_ciclo_anterior <> 0
)
select
    f.cct,
    f.id_ciclo,
    f.target_variacion_matricula,
    e.target_esperado
from {{ ref('features_escuela') }} f
join esperado e using (cct, id_ciclo)
where abs(f.target_variacion_matricula - e.target_esperado) > 1e-12
