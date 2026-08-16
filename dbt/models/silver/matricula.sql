with source_data as (

    select
        {{ normalize_cct('cct') }} as cct,
        trim(cast(ciclo as text)) as ciclo,
        {{ normalize_cve_ent('entidad') }} as cve_ent,
        {{ normalize_cve_mun('entidad', 'municipio') }} as cve_mun,
        trim(cast(nivel as text)) as nivel,
        cast(alumnos_total as integer) as alumnos_total,
        cast(docentes_total as integer) as docentes_total,
        cast(grupos_total as integer) as grupos_total,
        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url

    from {{ source('bronze', 'formato911') }}

),

deduplicated as (

    select *,
        row_number() over (
            partition by cct, ciclo
            order by _ingested_at desc
        ) as _row_number

    from source_data

)

select
    cct,
    ciclo,
    cve_ent,
    cve_mun,
    nivel,
    alumnos_total,
    docentes_total,
    grupos_total,
    _ingested_at,
    _source,
    _source_url

from deduplicated

where _row_number = 1
