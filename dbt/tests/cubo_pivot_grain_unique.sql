-- Grano DB-08. Debe devolver 0 filas.
select
    cct,
    id_driver,
    id_ciclo,
    count(*) as filas
from {{ ref('cubo_pivot') }}
group by cct, id_driver, id_ciclo
having count(*) <> 1
