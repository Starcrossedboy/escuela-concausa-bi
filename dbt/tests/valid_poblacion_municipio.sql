with base as (

    select *
    from {{ ref('poblacion_municipio') }}

),

duplicados as (

    select
        cve_mun,
        anio,
        grupo_edad

    from base

    group by
        cve_mun,
        anio,
        grupo_edad

    having count(*) > 1

)

select
    'duplicate_grain' as regla,
    concat_ws('|', cve_mun, anio::text, grupo_edad) as valor
from duplicados

union all

select
    'cve_ent_format' as regla,
    cve_ent as valor
from base
where cve_ent is not null
  and cve_ent !~ '^[0-9]{2}$'

union all

select
    'cve_mun_format' as regla,
    cve_mun as valor
from base
where cve_mun is not null
  and cve_mun !~ '^[0-9]{5}$'

union all

select
    'poblacion_negativa' as regla,
    poblacion::text as valor
from base
where poblacion is not null
  and poblacion < 0
