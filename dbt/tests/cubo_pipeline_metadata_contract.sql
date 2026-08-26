-- SIN_DATO implica ausencia real (NULL), nunca cero; OK exige metadata completa.
select *
from {{ ref('cubo_pipeline') }}
where
    (
        cobertura_pipeline = 'SIN_DATO'
        and (
            filas is not null
            or fecha_ingesta is not null
            or _ingested_at is not null
            or source_url is not null
        )
    )
    or
    (
        cobertura_pipeline = 'OK'
        and (
            filas is null
            or filas <= 0
            or fecha_ingesta is null
            or _ingested_at is null
            or source_url is null
        )
    )
