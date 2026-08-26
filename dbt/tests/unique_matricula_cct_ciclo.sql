select
    cct,
    ciclo,
    count(*) as registros

from {{ ref('matricula') }}

group by
    cct,
    ciclo

having count(*) > 1
