-- Contrato runtime C3. Debe devolver 0 filas.
select
    cct,
    id_ciclo,
    count(*) as filas
from {{ source('gold_ml_runtime', 'recomendaciones') }}
group by cct, id_ciclo
having count(*) <> 1
