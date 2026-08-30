-- US-113 / DB-03. Debe devolver 0 filas.
-- Valida cobertura observada y ML sin convertir ausencia a cero.
select *
from {{ ref('cubo_escuela_360') }}
where
    (d1_cobertura = 'SIN_DATO' and d1 is not null)
    or (d1_cobertura = 'OK' and d1 is null)
    or (d2_cobertura = 'SIN_DATO' and d2 is not null)
    or (d2_cobertura = 'OK' and d2 is null)
    or (d3_cobertura = 'SIN_DATO' and d3 is not null)
    or (d3_cobertura = 'OK' and d3 is null)
    or (d4_cobertura = 'SIN_DATO' and d4 is not null)
    or (d4_cobertura = 'OK' and d4 is null)
    or (d5_cobertura = 'SIN_DATO' and d5 is not null)
    or (d5_cobertura = 'OK' and d5 is null)
    or (d6_cobertura = 'SIN_DATO' and d6 is not null)
    or (d6_cobertura = 'OK' and d6 is null)

    or (cobertura_prediccion = 'SIN_DATO'
        and (
            indice_riesgo is not null
            or en_riesgo is not null
            or variacion_proyectada is not null
            or probabilidad is not null
        )
    )
    or (cobertura_prediccion = 'OK' and indice_riesgo is null)

    or (cobertura_recomendacion = 'SIN_DATO'
        and (
            driver_dominante is not null
            or nombre_driver is not null
            or recomendacion is not null
            or prioridad is not null
        )
    )
    or (cobertura_recomendacion = 'OK'
        and (
            driver_dominante is null
            or nombre_driver is null
            or recomendacion is null
            or prioridad is null
        )
    )
