with observaciones as (

    select
        cast(id_estacion as integer) as id_estacion,
        upper(nullif(btrim(cast(parametro as text)), '')) as parametro,
        cast(fecha as date) as fecha,
        cast(hora as integer) as hora,
        cast(valor as double precision) as valor,
        cast(val as integer) as dato_valido,
        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url

    from {{ source('bronze', 'sinaica_observaciones') }}

),

estaciones as (

    select
        cast(id as integer) as id_estacion,
        nullif(btrim(cast(nombre as text)), '') as nombre_estacion,
        nullif(btrim(cast("municipioId" as text)), '') as municipio_id_origen,
        cast(latitud as double precision) as latitud,
        cast(longitud as double precision) as longitud

    from {{ source('bronze', 'sinaica_estaciones') }}

),

joined as (

    select
        o.id_estacion,
        e.nombre_estacion,
        o.parametro,
        o.fecha,
        o.hora,
        o.valor,
        o.dato_valido,
        e.municipio_id_origen,
        e.latitud,
        e.longitud,
        o._ingested_at,
        o._source,
        o._source_url

    from observaciones o
    left join estaciones e
        on o.id_estacion = e.id_estacion

),

deduplicated as (

    select *,
        row_number() over (
            partition by id_estacion, parametro, fecha, hora
            order by _ingested_at desc
        ) as _row_number

    from joined

)

select
    id_estacion,
    nombre_estacion,
    parametro,
    fecha,
    hora,
    valor,
    dato_valido,
    municipio_id_origen,
    latitud,
    longitud,
    _ingested_at,
    _source,
    _source_url

from deduplicated

where _row_number = 1
