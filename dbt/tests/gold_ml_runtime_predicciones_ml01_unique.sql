-- ML-01 debe ser único por la llave correspondiente a su grano DEC-010.
-- El runtime legacy sin discriminador se interpreta como grano=escuela.
with normalizadas as (
    select
        coalesce(nullif(to_jsonb(p)->>'grano', ''), 'escuela') as grano,
        nullif(to_jsonb(p)->>'cct', '') as cct,
        nullif(to_jsonb(p)->>'cve_mun', '') as cve_mun,
        nullif(to_jsonb(p)->>'nivel', '') as nivel,
        p.id_ciclo
    from {{ source('gold_ml_runtime', 'predicciones') }} p
    where p.modelo = 'ML-01'
)

select
    grano,
    cct,
    cve_mun,
    nivel,
    id_ciclo,
    count(*) as filas
from normalizadas
group by grano, cct, cve_mun, nivel, id_ciclo
having count(*) <> 1
