-- Grano cct x id_ciclo: driver_dominante no debe romper la unicidad de la tabla.
select cct, id_ciclo, count(*) as filas
from {{ ref('features_escuela') }}
group by cct, id_ciclo
having count(*) > 1
