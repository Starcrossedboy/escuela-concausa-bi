-- Decisión canónica coordinada en US-111: Silver expone `ciclo`; Gold conserva
-- `id_ciclo` como PK/FK del esquema estrella. El alias de abajo es intencional.
with ciclos as (

    select distinct
        ciclo as id_ciclo
    from {{ ref('matricula') }}

)

select
    id_ciclo,
    id_ciclo                                  as ciclo,
    cast(split_part(id_ciclo, '-', 1) as int) as anio_inicio,
    cast(split_part(id_ciclo, '-', 2) as int) as anio_fin
from ciclos
