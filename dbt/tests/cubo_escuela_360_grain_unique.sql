-- US-113 / DB-03. Debe devolver 0 filas.
select
    cct,
    id_ciclo,
    count(*) as filas
from {{ ref('cubo_escuela_360') }}
group by cct, id_ciclo
having count(*) <> 1
