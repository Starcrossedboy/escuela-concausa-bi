-- Grano DB-09. Debe devolver 0 filas.
select
    cct,
    id_ciclo,
    count(*) as filas
from {{ ref('cubo_recomendaciones') }}
group by cct, id_ciclo
having count(*) <> 1
