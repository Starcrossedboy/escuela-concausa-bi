-- NOTA (merge 2026-08-18, Diana): Data_Model.md §5.1 documenta la columna como `id_ciclo`,
-- pero silver.matricula (US-111, Deni) la entrega como `ciclo`. Se aliasea aquí para no
-- tocar el modelo de Deni sin coordinar; pendiente decidir con ella/Edgar cuál nombre es
-- el canónico y, si es `ciclo`, actualizar Data_Model.md §5.1 (es fuente de verdad, regla 7).
with ciclos as (

    select distinct
        ciclo as id_ciclo
    from {{ source('silver', 'matricula') }}

)

select
    id_ciclo,
    id_ciclo                                  as ciclo,
    cast(split_part(id_ciclo, '-', 1) as int) as anio_inicio,
    cast(split_part(id_ciclo, '-', 2) as int) as anio_fin
from ciclos
