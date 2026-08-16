with source_data as (

    select
        {{ normalize_cct('cct') }} as cct,
        {{ normalize_binary_driver('agua_red') }} as agua,
        {{ normalize_binary_driver('drenaje') }} as drenaje,
        {{ normalize_binary_driver('electricidad') }} as electricidad,
        {{ normalize_binary_driver('sanitarios') }} as sanitarios,
        {{ normalize_binary_driver('internet') }} as internet,
        {{ normalize_binary_driver('computadoras') }} as computadoras,
        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url

    from {{ source('bronze', 'cemabe') }}

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
    agua,
    drenaje,
    electricidad,
    sanitarios,
    internet,
    computadoras,
    _ingested_at,
    _source,
    _source_url

from deduplicated

where _row_number = 1
