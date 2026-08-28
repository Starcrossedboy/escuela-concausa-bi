-- Grano fuente × fecha_ingesta. Debe devolver 0 filas.
select
    fuente,
    fecha_ingesta,
    count(*) as filas_grano
from {{ ref('cubo_pipeline') }}
group by fuente, fecha_ingesta
having count(*) <> 1
