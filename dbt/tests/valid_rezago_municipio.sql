with base as (

    select *
    from {{ ref('rezago_municipio') }}

),

duplicados as (

    select
        cve_mun,
        periodo_medicion

    from base

    group by
        cve_mun,
        periodo_medicion

    having count(*) > 1

)

select
    'duplicate_grain' as regla,
    concat_ws('|', cve_mun, periodo_medicion::text) as valor
from duplicados

union all

select
    'cve_mun_format' as regla,
    cve_mun as valor
from base
where cve_mun is not null
  and cve_mun !~ '^[0-9]{5}$'

union all

select
    'pobreza_pct_fuera_rango' as regla,
    pobreza_pct::text as valor
from base
where pobreza_pct is not null
  and pobreza_pct not between 0 and 100

union all

select
    'indice_cobertura_inconsistente' as regla,
    cve_mun as valor
from base
where
      (indice_rezago_social is null
       and indice_rezago_social_cobertura <> 'SIN_DATO')
   or (indice_rezago_social is not null
       and indice_rezago_social_cobertura <> 'OK')

union all

select
    'pobreza_cobertura_inconsistente' as regla,
    cve_mun as valor
from base
where
      (pobreza_pct is null
       and pobreza_pct_cobertura <> 'SIN_DATO')
   or (pobreza_pct is not null
       and pobreza_pct_cobertura <> 'OK')
