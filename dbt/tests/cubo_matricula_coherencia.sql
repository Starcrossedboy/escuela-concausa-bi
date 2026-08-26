select *
from {{ ref('cubo_matricula') }}
where
    escuelas <= 0
    or matricula_total < 0
    or cobertura_matricula <> 'OK'
    or escuelas_con_prediccion < 0
    or escuelas_con_prediccion > escuelas
    or (
        escuelas_con_prediccion = 0
        and (
            suma_variacion_proyectada is not null
            or cobertura_prediccion <> 'SIN_DATO'
        )
    )
    or (
        escuelas_con_prediccion > 0
        and (
            suma_variacion_proyectada is null
            or cobertura_prediccion <> 'OK'
        )
    )
