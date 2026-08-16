with base as (

    select *
    from {{ ref('agua_region') }}

),

duplicados as (

    select
        id_punto,
        indicador,
        fecha

    from base

    group by
        id_punto,
        indicador,
        fecha

    having count(*) > 1

)

select
    'duplicate_grain' as regla,
    concat_ws(
        '|',
        id_punto,
        indicador,
        fecha::text
    ) as valor
from duplicados

union all

select
    'latitud_fuera_rango' as regla,
    latitud::text as valor
from base
where latitud is not null
  and latitud not between -90 and 90

union all

select
    'longitud_fuera_rango' as regla,
    longitud::text as valor
from base
where longitud is not null
  and longitud not between -180 and 180
