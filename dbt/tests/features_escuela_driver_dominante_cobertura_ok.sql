-- driver_dominante siempre debe apuntar a un driver con cobertura 'OK' -- nunca a uno en
-- SIN_DATO (Andrés González Habib/C3, especificación US-302 del 2026-08-28).
with base as (

    select *
    from {{ ref('features_escuela') }}
    where driver_dominante is not null

)

select cct, id_ciclo, driver_dominante
from base
where
    (driver_dominante = 'D1' and d1_cobertura <> 'OK')
    or (driver_dominante = 'D2' and d2_cobertura <> 'OK')
    or (driver_dominante = 'D3' and d3_cobertura <> 'OK')
    or (driver_dominante = 'D4' and d4_cobertura <> 'OK')
    or (driver_dominante = 'D5' and d5_cobertura <> 'OK')
    or (driver_dominante = 'D6' and d6_cobertura <> 'OK')
