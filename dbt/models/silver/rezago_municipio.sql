with source_data as (

    select
        {{ normalize_cve_mun_standalone('cve_mun') }} as cve_mun,
        nullif(btrim(cast(entidad as text)), '') as entidad,
        nullif(btrim(cast(municipio as text)), '') as municipio,

        cast({{ var('coneval_periodo_medicion') }} as integer) as periodo_medicion,

        case
            when indice_rezago_social is null
              or btrim(cast(indice_rezago_social as text)) = ''
              or upper(btrim(cast(indice_rezago_social as text))) = 'SIN_DATO'
                then null
            else cast(indice_rezago_social as double precision)
        end as indice_rezago_social,

        case
            when indice_rezago_social is null
              or btrim(cast(indice_rezago_social as text)) = ''
              or upper(btrim(cast(indice_rezago_social as text))) = 'SIN_DATO'
                then 'SIN_DATO'
            else 'OK'
        end as indice_rezago_social_cobertura,

        case
            when grado_rezago is null
              or btrim(cast(grado_rezago as text)) = ''
                then 'SIN_DATO'
            else upper(btrim(cast(grado_rezago as text)))
        end as grado_rezago,

        case
            when pobreza_pct is null
              or btrim(cast(pobreza_pct as text)) = ''
              or upper(btrim(cast(pobreza_pct as text))) = 'SIN_DATO'
                then null
            else cast(pobreza_pct as double precision)
        end as pobreza_pct,

        case
            when pobreza_pct is null
              or btrim(cast(pobreza_pct as text)) = ''
              or upper(btrim(cast(pobreza_pct as text))) = 'SIN_DATO'
                then 'SIN_DATO'
            else 'OK'
        end as pobreza_pct_cobertura,

        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url

    from {{ source('bronze', 'coneval') }}

),

deduplicated as (

    select *,
        row_number() over (
            partition by cve_mun, periodo_medicion
            order by _ingested_at desc
        ) as _row_number

    from source_data

)

select
    cve_mun,
    entidad,
    municipio,
    periodo_medicion,
    indice_rezago_social,
    indice_rezago_social_cobertura,
    grado_rezago,
    pobreza_pct,
    pobreza_pct_cobertura,
    _ingested_at,
    _source,
    _source_url

from deduplicated

where _row_number = 1
