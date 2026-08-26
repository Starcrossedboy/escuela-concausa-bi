-- Contrato runtime DEC-010. Debe devolver 0 filas.
-- to_jsonb() conserva compatibilidad con el runtime legacy sin grano/cve_mun/nivel.
with normalizadas as (
    select
        coalesce(nullif(to_jsonb(p)->>'grano', ''), 'escuela') as grano,
        nullif(to_jsonb(p)->>'cct', '') as cct,
        nullif(to_jsonb(p)->>'cve_mun', '') as cve_mun,
        nullif(to_jsonb(p)->>'nivel', '') as nivel,
        p.id_ciclo,
        p.modelo
    from {{ source('gold_ml_runtime', 'predicciones') }} p
)

select
    grano,
    cct,
    cve_mun,
    nivel,
    id_ciclo,
    modelo,
    count(*) as filas
from normalizadas
group by grano, cct, cve_mun, nivel, id_ciclo, modelo
having count(*) <> 1
