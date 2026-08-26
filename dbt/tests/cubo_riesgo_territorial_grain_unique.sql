select
    cve_mun, nivel, id_ciclo, count(*) as filas
from {{ ref('cubo_riesgo_territorial') }}
group by cve_mun, nivel, id_ciclo
having count(*) <> 1
