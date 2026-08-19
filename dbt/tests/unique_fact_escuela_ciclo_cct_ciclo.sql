select
    cct,
    id_ciclo,
    count(*) as registros

from {{ ref('fact_escuela_ciclo') }}

group by
    cct,
    id_ciclo

having count(*) > 1