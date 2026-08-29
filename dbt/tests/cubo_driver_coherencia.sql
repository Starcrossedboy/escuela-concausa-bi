-- Cero real vs SIN_DATO y denominadores. Debe devolver 0 filas.
select *
from {{ ref('cubo_driver') }}
where
    total_escuelas <= 0
    or escuelas_con_recomendacion < 0
    or escuelas_con_recomendacion > total_escuelas
    or escuelas_sin_recomendacion <> total_escuelas - escuelas_con_recomendacion
    or (
        escuelas_con_recomendacion = 0
        and (
            escuelas_driver is not null
            or cobertura_recomendacion <> 'SIN_DATO'
        )
    )
    or (
        escuelas_con_recomendacion > 0
        and (
            escuelas_driver is null
            or escuelas_driver < 0
            or escuelas_driver > escuelas_con_recomendacion
            or cobertura_recomendacion <> 'OK'
        )
    )
