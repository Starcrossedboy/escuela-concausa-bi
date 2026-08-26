-- Contrato de llave dual DEC-010. Debe devolver 0 filas.
-- Legacy: si no existe grano, to_jsonb() devuelve NULL y se interpreta como escuela.
with normalizadas as (
    select
        p.*,
        coalesce(nullif(to_jsonb(p)->>'grano', ''), 'escuela') as grano_normalizado,
        nullif(to_jsonb(p)->>'cct', '') as cct_normalizado,
        nullif(to_jsonb(p)->>'cve_mun', '') as cve_mun_normalizado,
        nullif(to_jsonb(p)->>'nivel', '') as nivel_normalizado
    from {{ source('gold_ml_runtime', 'predicciones') }} p
)

select *
from normalizadas
where not (
    (
        grano_normalizado = 'escuela'
        and cct_normalizado is not null
        and cve_mun_normalizado is null
        and nivel_normalizado is null
    )
    or
    (
        grano_normalizado = 'municipio_nivel'
        and cct_normalizado is null
        and cve_mun_normalizado is not null
        and nivel_normalizado is not null
    )
)
