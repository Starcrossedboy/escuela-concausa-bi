select
    cve_mun, nivel, id_ciclo, count(*) as filas
from {{ ref('cubo_matricula') }}
group by cve_mun, nivel, id_ciclo
having count(*) <> 1
