with ciclos as (

    select distinct
        id_ciclo
    from {{ source('silver', 'matricula') }}

)

select
    id_ciclo,
    id_ciclo                                  as ciclo,
    cast(split_part(id_ciclo, '-', 1) as int) as anio_inicio,
    cast(split_part(id_ciclo, '-', 2) as int) as anio_fin
from ciclos
