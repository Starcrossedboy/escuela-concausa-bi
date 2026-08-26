-- Coherencia de componentes y banderas. Debe devolver 0 filas.
select *
from {{ ref('cubo_comparador_municipio') }}
where
    escuelas <= 0
    or escuelas_con_d1 < 0 or escuelas_con_d1 > escuelas
    or escuelas_con_d2 < 0 or escuelas_con_d2 > escuelas
    or escuelas_con_d3 < 0 or escuelas_con_d3 > escuelas
    or escuelas_con_d4 < 0 or escuelas_con_d4 > escuelas
    or escuelas_con_d5 < 0 or escuelas_con_d5 > escuelas
    or escuelas_con_d6 < 0 or escuelas_con_d6 > escuelas
    or (escuelas_con_d1 = 0 and (suma_d1 is not null or cobertura_d1 <> 'SIN_DATO'))
    or (escuelas_con_d1 > 0 and (suma_d1 is null or cobertura_d1 <> 'OK'))
    or (escuelas_con_d2 = 0 and (suma_d2 is not null or cobertura_d2 <> 'SIN_DATO'))
    or (escuelas_con_d2 > 0 and (suma_d2 is null or cobertura_d2 <> 'OK'))
    or (escuelas_con_d3 = 0 and (suma_d3 is not null or cobertura_d3 <> 'SIN_DATO'))
    or (escuelas_con_d3 > 0 and (suma_d3 is null or cobertura_d3 <> 'OK'))
    or (escuelas_con_d4 = 0 and (suma_d4 is not null or cobertura_d4 <> 'SIN_DATO'))
    or (escuelas_con_d4 > 0 and (suma_d4 is null or cobertura_d4 <> 'OK'))
    or (escuelas_con_d5 = 0 and (suma_d5 is not null or cobertura_d5 <> 'SIN_DATO'))
    or (escuelas_con_d5 > 0 and (suma_d5 is null or cobertura_d5 <> 'OK'))
    or (escuelas_con_d6 = 0 and (suma_d6 is not null or cobertura_d6 <> 'SIN_DATO'))
    or (escuelas_con_d6 > 0 and (suma_d6 is null or cobertura_d6 <> 'OK'))
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
