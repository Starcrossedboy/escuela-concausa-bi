-- Grano DEC-009. Debe devolver 0 filas.
select
    cve_mun,
    nivel,
    id_driver,
    id_ciclo,
    count(*) as filas
from {{ ref('cubo_completitud') }}
group by cve_mun, nivel, id_driver, id_ciclo
having count(*) <> 1
