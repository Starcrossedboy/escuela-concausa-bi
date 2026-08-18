with base as (

    select *
    from {{ ref('delitos_municipio') }}

),

duplicados as (

    select
        cve_mun,
        anio,
        mes,
        tipo_delito

    from base

    group by
        cve_mun,
        anio,
        mes,
        tipo_delito

    having count(*) > 1

)

select
    'duplicate_grain' as regla,
    concat_ws('|', cve_mun, anio::text, mes::text, tipo_delito) as valor
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
    'mes_fuera_rango' as regla,
    mes::text as valor
from base
where mes is not null
  and mes not between 1 and 12

union all

select
    'conteo_negativo' as regla,
    conteo::text as valor
from base
where conteo is not null
  and conteo < 0
