-- Cada municipio × nivel × ciclo debe tener exactamente D1..D6.
select
    cve_mun,
    nivel,
    id_ciclo,
    count(*) as filas,
    count(distinct id_driver) as drivers
from {{ ref('cubo_completitud') }}
group by cve_mun, nivel, id_ciclo
having count(*) <> 6 or count(distinct id_driver) <> 6
