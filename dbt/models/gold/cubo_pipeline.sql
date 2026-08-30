{{ config(materialized='materialized_view') }}

-- US-113 / DB-10
-- Grano canónico: fuente × fecha_ingesta.
-- `filas` es un componente aditivo: downstream debe consumir SUM(filas).
-- Una fuente ausente conserva una fila de catálogo con metadata NULL y SIN_DATO;
-- la ausencia nunca se representa como cero.

with fuentes_esperadas(id_fuente, fuente) as (
    values
        ('DS-01', 'DS-01_FORMATO911'),
        ('DS-02', 'DS-02_CATALOGO_CCT'),
        ('DS-03', 'DS-03_CEMABE'),
        ('DS-04', 'DS-04_SESNSP'),
        ('DS-05', 'DS-05_SINAICA'),
        ('DS-06', 'DS-06_CONAGUA_SINA'),
        ('DS-07', 'DS-07_CONEVAL'),
        ('DS-08', 'DS-08_CONAPO')
),

eventos as (
    select 'DS-01'::text as id_fuente, _source as fuente, _ingested_at, _source_url
    from {{ ref('matricula') }}
    where _source = 'DS-01_FORMATO911'

    union all
    select 'DS-02', _source, _ingested_at, _source_url
    from {{ ref('escuela') }}
    where _source = 'DS-02_CATALOGO_CCT'

    union all
    select 'DS-03', _source, _ingested_at, _source_url
    from {{ ref('cemabe') }}
    where _source = 'DS-03_CEMABE'

    union all
    select 'DS-04', _source, _ingested_at, _source_url
    from {{ ref('delitos_municipio') }}
    where _source = 'DS-04_SESNSP'

    union all
    select 'DS-05', _source, _ingested_at, _source_url
    from {{ ref('aire_estacion') }}
    where _source = 'DS-05_SINAICA'

    union all
    select 'DS-06', _source, _ingested_at, _source_url
    from {{ ref('agua_region') }}
    where _source = 'DS-06_CONAGUA_SINA'

    union all
    select 'DS-07', _source, _ingested_at, _source_url
    from {{ ref('rezago_municipio') }}
    where _source = 'DS-07_CONEVAL'

    union all
    select 'DS-08', _source, _ingested_at, _source_url
    from {{ ref('poblacion_municipio') }}
    where _source = 'DS-08_CONAPO'
),

agregado as (
    select
        id_fuente,
        fuente,
        cast(_ingested_at as date) as fecha_ingesta,
        count(*)::bigint as filas,
        max(_ingested_at) as _ingested_at,
        max(nullif(_source_url, '')) as source_url
    from eventos
    group by id_fuente, fuente, cast(_ingested_at as date)
)

select
    e.id_fuente,
    e.fuente,
    a.fecha_ingesta,
    a.filas,
    a._ingested_at,
    a.source_url,
    case when a.filas is null then 'SIN_DATO' else 'OK' end as cobertura_pipeline
from fuentes_esperadas e
left join agregado a
    on e.id_fuente = a.id_fuente
    and e.fuente = a.fuente
