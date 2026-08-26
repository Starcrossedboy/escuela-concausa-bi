-- Cuando hay cobertura, la suma D1..D6 debe ser el total de recomendaciones.
with grupos as (
    select
        cve_mun,
        nivel,
        id_ciclo,
        min(escuelas_con_recomendacion) as denominador,
        sum(escuelas_driver) as numerador,
        min(cobertura_recomendacion) as cobertura_min,
        max(cobertura_recomendacion) as cobertura_max
    from {{ ref('cubo_driver') }}
    group by cve_mun, nivel, id_ciclo
)
select *
from grupos
where
    (denominador > 0 and (
        numerador <> denominador
        or cobertura_min <> 'OK'
        or cobertura_max <> 'OK'
    ))
    or
    (denominador = 0 and (
        numerador is not null
        or cobertura_min <> 'SIN_DATO'
        or cobertura_max <> 'SIN_DATO'
    ))
