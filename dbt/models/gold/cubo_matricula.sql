{{ config(materialized='materialized_view') }}

-- US-113 / DB-01 + DB-06
-- Grano canónico ratificado en DEC-009:
-- cve_mun × nivel × id_ciclo.
--
-- DB-01 conserva componentes observados aditivos del SQL semántico C2.
-- DB-06 agrega componentes aditivos de ML-01 al MISMO grano:
--   suma_variacion_proyectada / escuelas_con_prediccion
-- para que el promedio se calcule downstream sin promedio-de-promedios.
--
-- Una fila observada siempre tiene cobertura_matricula='OK'.
-- Una fila sin ML permanece con componentes ML NULL + cobertura_prediccion='SIN_DATO'.
-- Nunca se convierte una predicción ausente a 0.

with observado as (
    select
        f.cve_mun,
        dm.cve_ent,
        dm.nombre_municipio,
        dm.nombre_entidad,
        e.nivel,
        f.id_ciclo,
        dt.ciclo,
        dt.anio_inicio,

        count(distinct f.cct) as escuelas,
        sum(f.matricula_total) as matricula_total,
        -- FIX (2026-08-31, Diana/BUG-031): mismo defecto y mismo fix que cubo_comparador_municipio
        -- (ver ese archivo) -- este cubo alimenta DB-01/DB-06, también listados como afectados.
        sum(f.matricula_ciclo_anterior) as suma_matricula_anterior,
        sum(f.indice_completitud_drivers) as suma_completitud
    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    inner join {{ ref('dim_tiempo') }} dt
        on f.id_ciclo = dt.id_ciclo
    inner join {{ ref('dim_municipio') }} dm
        on f.cve_mun = dm.cve_mun

    group by
        f.cve_mun,
        dm.cve_ent,
        dm.nombre_municipio,
        dm.nombre_entidad,
        e.nivel,
        f.id_ciclo,
        dt.ciclo,
        dt.anio_inicio
),

prediccion as (
    select
        f.cve_mun,
        e.nivel,
        f.id_ciclo,

        sum(p.valor) as suma_variacion_proyectada,
        count(*) as escuelas_con_prediccion

    from {{ ref('fact_escuela_ciclo') }} f
    inner join {{ ref('dim_escuela') }} e
        on f.cct = e.cct
    inner join {{ source('gold_ml_runtime', 'predicciones') }} p
        on f.cct = p.cct
        and f.id_ciclo = p.id_ciclo
        and p.modelo = 'ML-01'
        and coalesce(nullif(to_jsonb(p)->>'grano', ''), 'escuela') = 'escuela'

    group by
        f.cve_mun,
        e.nivel,
        f.id_ciclo
)

select
    o.*,

    p.suma_variacion_proyectada,
    coalesce(p.escuelas_con_prediccion, 0) as escuelas_con_prediccion,

    'OK'::text as cobertura_matricula,

    case
        when coalesce(p.escuelas_con_prediccion, 0) = 0 then 'SIN_DATO'
        else 'OK'
    end as cobertura_prediccion

from observado o
left join prediccion p
    on o.cve_mun = p.cve_mun
    and o.nivel = p.nivel
    and o.id_ciclo = p.id_ciclo
