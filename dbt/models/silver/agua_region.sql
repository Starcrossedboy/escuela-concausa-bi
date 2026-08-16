with source_data as (

    select
        cast({{ adapter.quote(var('bronze_conagua_id_column')) }} as text) as id_punto,
        nullif(btrim(cast(region_hidrologica as text)), '') as region_hidrologica,
        cast(latitud as double precision) as latitud,
        cast(longitud as double precision) as longitud,
        upper(nullif(btrim(cast(indicador as text)), '')) as indicador,
        cast(valor as double precision) as valor,
        cast(fecha as date) as fecha,
        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url

    from {{ source('bronze', 'conagua') }}

),

deduplicated as (

    select *,
        row_number() over (
            partition by id_punto, indicador, fecha
            order by _ingested_at desc
        ) as _row_number

    from source_data

)

select
    id_punto,
    region_hidrologica,
    latitud,
    longitud,
    indicador,
    valor,
    fecha,
    _ingested_at,
    _source,
    _source_url

from deduplicated

where _row_number = 1
