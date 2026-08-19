-- gold.features_escuela (US-104) — contrato Célula 1 -> Célula 3 (Data_Model.md §5.3/§4.4).
-- Grano: CCT x ciclo. Fuente de la llave y del target: silver.matricula (US-111, Deni).
--
-- Estado de los 6 drivers en esta primera versión:
--   D1 pobreza          -- real, silver.rezago_municipio (DS-07) por cve_mun
--   D2 inseguridad       -- real, silver.delitos_municipio (DS-04) por cve_mun, agregado
--                            SIN alinear meses al ciclo escolar todavía (simplificación
--                            documentada abajo, pendiente de refinar)
--   D3 infraestructura   -- real, silver.cemabe (DS-03) por cct, ADR-005
--   D4 conectividad      -- real, silver.cemabe (DS-03) por cct, ADR-005
--   D5 agua              -- SIN_DATO explícito: CONAGUA (silver.agua_region) no trae cve_mun
--                            todavía, falta el join espacial/IDW que es alcance de US-105
--   D6 aire              -- SIN_DATO explícito: mismo motivo que D5, para SINAICA
--
-- D5/D6 en SIN_DATO no es un hueco escondido: es la regla del proyecto (Data_Model.md §3,
-- "SIN_DATO explícito, nunca cero ni nulo silencioso") aplicada honestamente a un join que
-- todavía no existe. Cuando US-105 entregue la interpolación IDW, se reemplaza aquí.
--
-- FIX (2026-08-19, Diana): Data_Model.md §7 es explícito -- "el filtro WHERE cve_ent IN
-- SCOPE_ENTIDADES se aplica únicamente en la frontera Silver -> Gold (Y EN FEATURES/MODELOS/
-- DASHBOARDS que derivan de Gold)". Esta tabla es Gold y es justo "features" -- debía llevar
-- el filtro desde el día 1 y no lo llevaba. Corregido aquí filtrando por cve_ent de
-- silver.matricula (mismo origen ya aceptado para cve_mun en esta tabla, ver nota de arriba).

with matricula_ciclo as (

    -- NOTA (US-104, Diana): igual que en dim_tiempo.sql, Data_Model.md §5.1/§6 documenta
    -- `matricula_total`, pero silver.matricula (US-111, Deni) la entrega como `alumnos_total`.
    -- Se aliasea aquí por consistencia con el fix ya aplicado en dim_tiempo.sql; sigue pendiente
    -- reconciliar el nombre canónico con Deni/Edgar y, si aplica, actualizar Data_Model.md.
    select
        cct,
        ciclo as id_ciclo,
        cve_mun,
        alumnos_total as matricula_total,
        cast(split_part(ciclo, '-', 1) as int) as anio_inicio
    from {{ source('silver', 'matricula') }}
    where cve_ent in {{ scope_entidades() }}

),

con_target as (

    select
        *,
        lag(matricula_total) over (
            partition by cct order by anio_inicio
        ) as matricula_ciclo_anterior
    from matricula_ciclo

),

base as (

    -- Sin ciclo anterior no hay target que entrenar (es la primera observación del cct);
    -- se excluye aquí, no se rellena con 0 (evitaría una fuga de "variación cero" falsa).
    select
        cct,
        id_ciclo,
        cve_mun,
        matricula_total,
        cast(matricula_total - matricula_ciclo_anterior as double precision)
            as target_variacion_matricula
    from con_target
    where matricula_ciclo_anterior is not null

),

-- D3/D4: infraestructura y conectividad, CEMABE por CCT (ADR-005)
cemabe_binarios as (

    select
        cct,
        case when drenaje in ('0', '1') then drenaje::numeric end as drenaje_num,
        case when electricidad in ('0', '1') then electricidad::numeric end as electricidad_num,
        case when sanitarios in ('0', '1') then sanitarios::numeric end as sanitarios_num,
        case when internet in ('0', '1') then internet::numeric end as internet_num,
        case when computadoras in ('0', '1') then computadoras::numeric end as computadoras_num
    from {{ source('silver', 'cemabe') }}

),

d3_d4 as (

    select
        cct,
        (coalesce(drenaje_num, 0) + coalesce(electricidad_num, 0) + coalesce(sanitarios_num, 0))
            / nullif(
                (case when drenaje_num is not null then 1 else 0 end)
                + (case when electricidad_num is not null then 1 else 0 end)
                + (case when sanitarios_num is not null then 1 else 0 end), 0)
            as d3_infraestructura,
        case
            when drenaje_num is not null or electricidad_num is not null
                 or sanitarios_num is not null then 'OK'
            else 'SIN_DATO'
        end as d3_cobertura,
        (coalesce(internet_num, 0) + coalesce(computadoras_num, 0))
            / nullif(
                (case when internet_num is not null then 1 else 0 end)
                + (case when computadoras_num is not null then 1 else 0 end), 0)
            as d4_conectividad,
        case
            when internet_num is not null or computadoras_num is not null then 'OK'
            else 'SIN_DATO'
        end as d4_cobertura
    from cemabe_binarios

),

-- D1: pobreza y rezago social, CONEVAL por municipio, último periodo_medicion disponible
rezago_ultimo as (

    select
        cve_mun,
        indice_rezago_social,
        indice_rezago_social_cobertura,
        row_number() over (
            partition by cve_mun order by periodo_medicion desc
        ) as _rn
    from {{ source('silver', 'rezago_municipio') }}

),

rezago_rango as (

    select min(indice_rezago_social) as min_val, max(indice_rezago_social) as max_val
    from rezago_ultimo
    where _rn = 1 and indice_rezago_social_cobertura = 'OK'

),

d1 as (

    select
        r.cve_mun,
        case
            when r.indice_rezago_social_cobertura = 'OK' and rg.max_val > rg.min_val
                then (r.indice_rezago_social - rg.min_val) / (rg.max_val - rg.min_val)
            when r.indice_rezago_social_cobertura = 'OK'
                then 0.5  -- todos los municipios con el mismo valor: normalizado al centro
            else null
        end as d1_pobreza,
        r.indice_rezago_social_cobertura as d1_cobertura
    from rezago_ultimo r
    cross join rezago_rango rg
    where r._rn = 1

),

-- D2: inseguridad, SESNSP por municipio. Suma de todos los delitos disponibles (todavía
-- sin alinear meses al ciclo escolar; simplificación a refinar cuando haya datos reales)
delitos_por_municipio as (

    select cve_mun, sum(conteo) as conteo_total
    from {{ source('silver', 'delitos_municipio') }}
    group by cve_mun

),

delitos_rango as (

    select min(conteo_total) as min_val, max(conteo_total) as max_val
    from delitos_por_municipio

),

d2 as (

    select
        d.cve_mun,
        case
            when dr.max_val > dr.min_val
                then (d.conteo_total - dr.min_val) / cast(dr.max_val - dr.min_val as double precision)
            else 0.5
        end as d2_inseguridad,
        'OK' as d2_cobertura
    from delitos_por_municipio d
    cross join delitos_rango dr

),

ensamblado as (

    select
        b.cct,
        b.id_ciclo,
        d1.d1_pobreza,
        coalesce(d1.d1_cobertura, 'SIN_DATO') as d1_cobertura,
        d2.d2_inseguridad,
        coalesce(d2.d2_cobertura, 'SIN_DATO') as d2_cobertura,
        dd.d3_infraestructura,
        coalesce(dd.d3_cobertura, 'SIN_DATO') as d3_cobertura,
        dd.d4_conectividad,
        coalesce(dd.d4_cobertura, 'SIN_DATO') as d4_cobertura,
        cast(null as double precision) as d5_agua,
        'SIN_DATO' as d5_cobertura,
        cast(null as double precision) as d6_aire,
        'SIN_DATO' as d6_cobertura,
        b.target_variacion_matricula
    from base b
    left join d3_d4 dd on dd.cct = b.cct
    left join d1 on d1.cve_mun = b.cve_mun
    left join d2 on d2.cve_mun = b.cve_mun

)

select
    cct,
    id_ciclo,
    d1_pobreza,
    d2_inseguridad,
    d3_infraestructura,
    d4_conectividad,
    d5_agua,
    d6_aire,
    d1_cobertura,
    d2_cobertura,
    d3_cobertura,
    d4_cobertura,
    d5_cobertura,
    d6_cobertura,
    (
        (case when d1_cobertura = 'OK' then 1 else 0 end)
        + (case when d2_cobertura = 'OK' then 1 else 0 end)
        + (case when d3_cobertura = 'OK' then 1 else 0 end)
        + (case when d4_cobertura = 'OK' then 1 else 0 end)
        + (case when d5_cobertura = 'OK' then 1 else 0 end)
        + (case when d6_cobertura = 'OK' then 1 else 0 end)
    ) / 6.0 as indice_completitud_drivers,
    target_variacion_matricula
from ensamblado