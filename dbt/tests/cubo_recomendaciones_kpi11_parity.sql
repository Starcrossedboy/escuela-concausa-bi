-- KPI-11: SUM(recomendacion_emitida) debe igualar COUNT(*) runtime.
with cubo as (
    select sum(recomendacion_emitida)::bigint as n
    from {{ ref('cubo_recomendaciones') }}
),
runtime as (
    select count(*)::bigint as n
    from {{ source('gold_ml_runtime', 'recomendaciones') }}
)
select cubo.n as cubo_n, runtime.n as runtime_n
from cubo cross join runtime
where cubo.n <> runtime.n
