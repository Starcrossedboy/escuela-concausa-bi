-- gold.dim_escuela (US-103) — Data_Model.md §4.2/§6. PK: cct. Acotado a SCOPE_ENTIDADES
-- (Data_Model.md §7): CDMX, Edomex, Nuevo León, Jalisco.
--
-- Identidad/georreferencia real de silver.escuela (DS-02, US-111 Deni) + infraestructura real
-- de silver.cemabe (DS-03) por cct, left join porque no todas las escuelas del catálogo tienen
-- todavía censo CEMABE (SIN_DATO explícito en ese caso, nunca 0 -- Data_Model.md §3).

with escuela as (

    select
        cct,
        nombre,
        nivel,
        sostenimiento,
        cve_ent,
        cve_mun,
        latitud,
        longitud
    from {{ source('silver', 'escuela') }}
    where cve_ent in {{ scope_entidades() }}

),

infraestructura as (

    select
        cct,
        agua,
        drenaje,
        electricidad,
        sanitarios,
        internet,
        computadoras
    from {{ source('silver', 'cemabe') }}

)

select
    e.cct,
    e.nombre,
    e.nivel,
    e.sostenimiento,
    e.latitud,
    e.longitud,
    e.cve_ent,
    e.cve_mun,
    coalesce(i.agua, 'SIN_DATO') as agua,
    coalesce(i.drenaje, 'SIN_DATO') as drenaje,
    coalesce(i.electricidad, 'SIN_DATO') as electricidad,
    coalesce(i.sanitarios, 'SIN_DATO') as sanitarios,
    coalesce(i.internet, 'SIN_DATO') as internet,
    coalesce(i.computadoras, 'SIN_DATO') as computadoras
from escuela e
left join infraestructura i on i.cct = e.cct