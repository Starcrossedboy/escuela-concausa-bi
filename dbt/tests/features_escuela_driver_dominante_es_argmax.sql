-- driver_dominante debe ser el driver con el valor MÁS ALTO entre los elegibles (cobertura
-- 'OK'), no solo cualquier driver con cobertura 'OK'. `greatest()` en Postgres ignora los NULL
-- y solo devuelve NULL si todos los argumentos lo son -- exactamente el comportamiento que
-- necesitamos para comparar contra un driver_dominante ya no-nulo.
with base as (

    select
        cct,
        id_ciclo,
        driver_dominante,
        greatest(
            case when d1_cobertura = 'OK' then d1_pobreza end,
            case when d2_cobertura = 'OK' then d2_inseguridad end,
            case when d3_cobertura = 'OK' then d3_infraestructura end,
            case when d4_cobertura = 'OK' then d4_conectividad end,
            case when d5_cobertura = 'OK' then d5_agua end,
            case when d6_cobertura = 'OK' then d6_aire end
        ) as valor_maximo,
        case driver_dominante
            when 'D1' then d1_pobreza
            when 'D2' then d2_inseguridad
            when 'D3' then d3_infraestructura
            when 'D4' then d4_conectividad
            when 'D5' then d5_agua
            when 'D6' then d6_aire
        end as valor_elegido
    from {{ ref('features_escuela') }}
    where driver_dominante is not null

)

select cct, id_ciclo, driver_dominante, valor_elegido, valor_maximo
from base
where valor_elegido is distinct from valor_maximo
