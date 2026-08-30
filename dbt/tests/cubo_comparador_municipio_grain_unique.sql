-- Grano ratificado por DEC-008. Debe devolver 0 filas.
select
    cve_mun,
    nivel,
    id_ciclo,
    count(*) as filas
from {{ ref('cubo_comparador_municipio') }}
group by cve_mun, nivel, id_ciclo
having count(*) <> 1
