with source_data as (

    select
        {{ normalize_cct('cct') }} as cct,
        nullif(trim(cast(nombre as text)), '') as nombre,
        nullif(trim(cast(nivel as text)), '') as nivel,
        nullif(trim(cast(sostenimiento as text)), '') as sostenimiento,
        {{ normalize_cve_ent('entidad') }} as cve_ent,
        {{ normalize_cve_mun('entidad', 'municipio') }} as cve_mun,
        -- FIX (2026-08-19, Diana/US-103): Data_Model.md §6 documenta lat/lon como nullable
        -- ("Sí" en Nulos) -- una escuela sin georreferencia todavía es un caso real y
        -- esperado, no un error. El cast directo sin nullif() tronaba con "" (invalid input
        -- syntax for type double precision), en vez de producir NULL. Mismo patrón que ya
        -- se usa arriba para nombre/nivel/sostenimiento.
        nullif(trim(cast(latitud as text)), '')::double precision as latitud,
        nullif(trim(cast(longitud as text)), '')::double precision as longitud,
        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url

    from {{ source('bronze', 'cct') }}

),

deduplicated as (

    select *,
        row_number() over (
            partition by cct
            order by _ingested_at desc
        ) as _row_number

    from source_data

)

select
    cct,
    nombre,
    nivel,
    sostenimiento,
    cve_ent,
    cve_mun,
    latitud,
    longitud,
    _ingested_at,
    _source,
    _source_url

from deduplicated

where _row_number = 1
