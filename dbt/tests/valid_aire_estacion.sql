with base as (

    select *
    from {{ ref('aire_estacion') }}

),

duplicados as (

    select
        id_estacion,
        parametro,
        fecha,
        hora

    from base

    group by
        id_estacion,
        parametro,
        fecha,
        hora

    having count(*) > 1

)

select
    'duplicate_grain' as regla,
    concat_ws(
        '|',
        id_estacion::text,
        parametro,
        fecha::text,
        hora::text
    ) as valor
from duplicados

union all

select
    'hora_fuera_rango' as regla,
    hora::text as valor
from base
where hora is not null
  and hora not between 0 and 23

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
