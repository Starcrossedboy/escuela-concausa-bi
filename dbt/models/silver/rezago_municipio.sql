with irs_base as (

    select
        (case when (case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end) is null or (case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end) is null then null when length((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end)) = 5  and left((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end), 2) = lpad((case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end), 2, '0') then (case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end) when length((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end)) between 1 and 3 then lpad((case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end), 2, '0') || lpad((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end), 3, '0') else null end) as cve_mun,
        nullif(btrim(cast("c_9b370f449788" as text)), '') as entidad,
        nullif(btrim(cast("c_9e8609cad84d" as text)), '') as municipio,
        cast("_periodo_medicion" as integer) as periodo_medicion,

        case
            when "c_5d0523b1d4a3" is null or btrim(cast("c_5d0523b1d4a3" as text)) = '' then null
            else cast("c_5d0523b1d4a3" as double precision)
        end as indice_rezago_social,

        case
            when "c_5d0523b1d4a3" is null or btrim(cast("c_5d0523b1d4a3" as text)) = '' then 'SIN_DATO'
            else 'OK'
        end as indice_rezago_social_cobertura,

        case
            when "c_91fd46c9babe" is null or btrim(cast("c_91fd46c9babe" as text)) = '' then 'SIN_DATO'
            else upper(btrim(cast("c_91fd46c9babe" as text)))
        end as grado_rezago,

        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url,

        row_number() over (
            partition by
                (case when (case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end) is null or (case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end) is null then null when length((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end)) = 5  and left((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end), 2) = lpad((case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end), 2, '0') then (case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end) when length((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end)) between 1 and 3 then lpad((case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end), 2, '0') || lpad((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end), 3, '0') else null end),
                cast("_periodo_medicion" as integer)
            order by cast(_ingested_at as timestamp) desc
        ) as _row_number

    from {{ source('bronze', 'coneval_irs') }}
    where (case when (case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end) is null or (case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end) is null then null when length((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end)) = 5  and left((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end), 2) = lpad((case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end), 2, '0') then (case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end) when length((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end)) between 1 and 3 then lpad((case when btrim(cast("c_b9548dbd414b" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_b9548dbd414b" as text)), '[.]0+$', '') else null end), 2, '0') || lpad((case when btrim(cast("c_deef5d1bd71a" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_deef5d1bd71a" as text)), '[.]0+$', '') else null end), 3, '0') else null end) ~ '^[0-9]{5}$'

),

irs as (
    select * from irs_base where _row_number = 1
),

pobreza_base as (

    select
        (case when (case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end) is null or (case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end) is null then null when length((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end)) = 5  and left((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end), 2) = lpad((case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end), 2, '0') then (case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end) when length((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end)) between 1 and 3 then lpad((case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end), 2, '0') || lpad((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end), 3, '0') else null end) as cve_mun,
        nullif(btrim(cast("c_9b370f449788" as text)), '') as entidad,
        nullif(btrim(cast("c_9e8609cad84d" as text)), '') as municipio,
        cast("_periodo_medicion" as integer) as periodo_medicion,

        case
            when "c_1a3c72ae6dd1" is null
              or btrim(cast("c_1a3c72ae6dd1" as text)) = ''
              or regexp_replace(lower(btrim(cast("c_1a3c72ae6dd1" as text))), '[^a-z0-9]+', '', 'g') = 'nd'
                then null
            else cast("c_1a3c72ae6dd1" as double precision)
        end as pobreza_pct,

        case
            when "c_1a3c72ae6dd1" is null
              or btrim(cast("c_1a3c72ae6dd1" as text)) = ''
              or regexp_replace(lower(btrim(cast("c_1a3c72ae6dd1" as text))), '[^a-z0-9]+', '', 'g') = 'nd'
                then 'SIN_DATO'
            else 'OK'
        end as pobreza_pct_cobertura,

        cast(_ingested_at as timestamp) as _ingested_at,
        cast(_source as text) as _source,
        cast(_source_url as text) as _source_url,

        row_number() over (
            partition by
                (case when (case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end) is null or (case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end) is null then null when length((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end)) = 5  and left((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end), 2) = lpad((case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end), 2, '0') then (case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end) when length((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end)) between 1 and 3 then lpad((case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end), 2, '0') || lpad((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end), 3, '0') else null end),
                cast("_periodo_medicion" as integer)
            order by cast(_ingested_at as timestamp) desc
        ) as _row_number

    from {{ source('bronze', 'coneval_pobreza') }}
    where (case when (case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end) is null or (case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end) is null then null when length((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end)) = 5  and left((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end), 2) = lpad((case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end), 2, '0') then (case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end) when length((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end)) between 1 and 3 then lpad((case when btrim(cast("c_9bd1a7aa7fca" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_9bd1a7aa7fca" as text)), '[.]0+$', '') else null end), 2, '0') || lpad((case when btrim(cast("c_764f3baf1395" as text)) ~ '^[0-9]+([.]0+)?$' then regexp_replace(btrim(cast("c_764f3baf1395" as text)), '[.]0+$', '') else null end), 3, '0') else null end) ~ '^[0-9]{5}$'

),

pobreza as (
    select * from pobreza_base where _row_number = 1
),

conformado as (

    select
        coalesce(i.cve_mun, p.cve_mun) as cve_mun,
        coalesce(i.entidad, p.entidad) as entidad,
        coalesce(i.municipio, p.municipio) as municipio,
        coalesce(i.periodo_medicion, p.periodo_medicion) as periodo_medicion,
        i.indice_rezago_social,
        coalesce(i.indice_rezago_social_cobertura, 'SIN_DATO') as indice_rezago_social_cobertura,
        coalesce(i.grado_rezago, 'SIN_DATO') as grado_rezago,
        p.pobreza_pct,
        coalesce(p.pobreza_pct_cobertura, 'SIN_DATO') as pobreza_pct_cobertura,
        greatest(i._ingested_at, p._ingested_at) as _ingested_at,
        'DS-07_CONEVAL'::text as _source,
        coalesce(i._source_url, p._source_url) as _source_url
    from irs i
    full outer join pobreza p
      on i.cve_mun = p.cve_mun
     and i.periodo_medicion = p.periodo_medicion
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
from conformado
