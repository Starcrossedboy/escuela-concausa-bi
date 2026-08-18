with source_data as (

    select
        {{ normalize_cve_ent('cve_ent') }} as cve_ent,
        {{ normalize_cve_mun('cve_ent', 'cve_mun') }} as cve_mun,
        cast(anio as integer) as anio,
        cast(mes as integer) as mes,
        nullif(btrim(cast(tipo_delito as text)), '') as tipo_delito,
        cast({{ var('bronze_sesnsp_count_column') }} as integer) as conteo,
        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url

    from {{ source('bronze', 'sesnsp') }}

),

deduplicated as (

    select *,
        row_number() over (
            partition by cve_mun, anio, mes, tipo_delito
            order by _ingested_at desc
        ) as _row_number

    from source_data

)

select
    cve_ent,
    cve_mun,
    anio,
    mes,
    tipo_delito,
    conteo,
    _ingested_at,
    _source,
    _source_url

from deduplicated

where _row_number = 1
