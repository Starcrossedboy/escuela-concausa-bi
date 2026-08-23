-- ML-01 debe ser único por CCT × ciclo para no multiplicar el pivot.
select
    cct,
    id_ciclo,
    count(*) as filas
from {{ source('gold_ml_runtime', 'predicciones') }}
where modelo = 'ML-01'
group by cct, id_ciclo
having count(*) <> 1
