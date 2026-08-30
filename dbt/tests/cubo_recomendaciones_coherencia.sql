-- Cobertura explícita DB-09. Debe devolver 0 filas.
select *
from {{ ref('cubo_recomendaciones') }}
where
    (
        cobertura_recomendacion = 'SIN_DATO'
        and (
            recomendacion_emitida <> 0
            or driver_dominante is not null
            or nombre_driver is not null
            or recomendacion is not null
            or prioridad is not null
        )
    )
    or
    (
        cobertura_recomendacion = 'OK'
        and (
            recomendacion_emitida <> 1
            or driver_dominante is null
            or nombre_driver is null
            or recomendacion is null
            or prioridad is null
        )
    )
