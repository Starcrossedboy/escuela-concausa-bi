-- Contrato runtime C3. Debe devolver 0 filas.
select
    cct,
    id_ciclo,
    modelo,
    count(*) as filas
from {{ source('gold_ml_runtime', 'predicciones') }}
group by cct, id_ciclo, modelo
having count(*) <> 1
