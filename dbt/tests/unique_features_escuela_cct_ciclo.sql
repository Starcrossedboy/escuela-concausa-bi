select
    cct,
    id_ciclo,
    count(*) as registros

from {{ ref('features_escuela') }}

group by
    cct,
    id_ciclo

having count(*) > 1