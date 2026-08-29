select *
from {{ ref('cubo_riesgo_territorial') }}
where
    escuelas <= 0
    or escuelas_con_prediccion < 0
    or escuelas_con_prediccion > escuelas
    or (
        escuelas_con_prediccion = 0
        and (
            suma_indice_riesgo is not null
            or escuelas_en_riesgo is not null
            or cobertura_riesgo <> 'SIN_DATO'
        )
    )
    or (
        escuelas_con_prediccion > 0
        and (
            suma_indice_riesgo is null
            or escuelas_en_riesgo is null
            or cobertura_riesgo <> 'OK'
        )
    )
