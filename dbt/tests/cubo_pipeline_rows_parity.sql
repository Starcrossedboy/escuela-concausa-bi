-- SUM(filas) debe coincidir con las filas Silver cuya metadata declara el SOURCE_NAME canónico.
with esperado as (
    select 'DS-01'::text as id_fuente, count(*)::bigint as filas from {{ ref('matricula') }} where _source = 'DS-01_FORMATO911'
    union all select 'DS-02', count(*)::bigint from {{ ref('escuela') }} where _source = 'DS-02_CATALOGO_CCT'
    union all select 'DS-03', count(*)::bigint from {{ ref('cemabe') }} where _source = 'DS-03_CEMABE'
    union all select 'DS-04', count(*)::bigint from {{ ref('delitos_municipio') }} where _source = 'DS-04_SESNSP'
    union all select 'DS-05', count(*)::bigint from {{ ref('aire_estacion') }} where _source = 'DS-05_SINAICA'
    union all select 'DS-06', count(*)::bigint from {{ source('bronze', 'conagua_presas') }} where _source = 'DS-06_CONAGUA_SINA'
    union all select 'DS-07', count(*)::bigint from {{ ref('rezago_municipio') }} where _source = 'DS-07_CONEVAL'
    union all select 'DS-08', count(*)::bigint from {{ ref('poblacion_municipio') }} where _source = 'DS-08_CONAPO'
),
obtenido as (
    select id_fuente, coalesce(sum(filas), 0)::bigint as filas
    from {{ ref('cubo_pipeline') }}
    group by id_fuente
)
select e.id_fuente, e.filas as esperado, o.filas as obtenido
from esperado e
inner join obtenido o using (id_fuente)
where e.filas <> o.filas
