-- Toda recomendación runtime debe pertenecer al hecho escolar Gold.
select
    r.cct,
    r.id_ciclo
from {{ source('gold_ml_runtime', 'recomendaciones') }} r
left join {{ ref('fact_escuela_ciclo') }} f
    on r.cct = f.cct
    and r.id_ciclo = f.id_ciclo
where f.cct is null
