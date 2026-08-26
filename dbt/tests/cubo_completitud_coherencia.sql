-- Componentes y cobertura. Debe devolver 0 filas.
select *
from {{ ref('cubo_completitud') }}
where
    total_escuelas < 0
    or escuelas_con_dato < 0
    or escuelas_sin_dato < 0
    or total_escuelas <> escuelas_con_dato + escuelas_sin_dato
    or (cobertura_driver = 'SIN_DATO' and escuelas_con_dato <> 0)
    or (cobertura_driver = 'OK' and escuelas_con_dato = 0)
