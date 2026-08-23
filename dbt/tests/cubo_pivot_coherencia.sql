-- Cobertura explícita del valor de driver. Debe devolver 0 filas.
select *
from {{ ref('cubo_pivot') }}
where
    (cobertura_driver = 'SIN_DATO' and valor_driver is not null)
    or
    (cobertura_driver = 'OK' and valor_driver is null)
    or
    (
        cobertura_prediccion = 'SIN_DATO'
        and (
            variacion_proyectada is not null
            or indice_riesgo is not null
            or probabilidad is not null
        )
    )
    or
    (
        cobertura_recomendacion = 'SIN_DATO'
        and (
            driver_dominante is not null
            or recomendacion is not null
            or prioridad is not null
        )
    )
