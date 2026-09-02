-- ADR-007: una matrícula previa cero no es divisible y debe bloquear el pipeline.
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
)
select cct, id_ciclo, matricula_total, matricula_ciclo_anterior
from serie
where matricula_ciclo_anterior = 0
