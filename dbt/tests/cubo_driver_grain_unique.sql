-- Grano DEC-009 candidato. Debe devolver 0 filas.
select
    id_driver,
    cve_mun,
    nivel,
    id_ciclo,
    count(*) as filas
from {{ ref('cubo_driver') }}
group by id_driver, cve_mun, nivel, id_ciclo
having count(*) <> 1
