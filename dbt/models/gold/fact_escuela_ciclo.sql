-- gold.fact_escuela_ciclo (US-103) — hecho central, Data_Model.md §4.1/§6. Grano: cct x
-- ciclo. Contiene únicamente hechos OBSERVADOS (nunca salidas de ML: indice_riesgo vive en
-- gold.predicciones, driver_dominante en gold.recomendaciones -- se consultan por JOIN).
--
-- Acotado a SCOPE_ENTIDADES (Data_Model.md §7) heredado del INNER JOIN contra dim_escuela
-- (que ya viene filtrada) -- no se repite el filtro aquí, un solo lugar de verdad.
--
-- cve_mun se toma de dim_escuela (origen documentado DS-02, Data_Model.md §6), NO de
-- silver.matricula directamente -- a diferencia de gold.features_escuela (US-104), que por ser
-- tabla de entrenamiento ML tomó cve_mun de DS-01 como simplificación aceptada en su momento.
--
-- D1-D4 replican la misma lógica real que gold.features_escuela (mismas fuentes Silver,
-- mismo ADR-004 para D3/D4). D5 agua y D6 aire quedan en SIN_DATO explícito por el mismo
-- motivo documentado ahí: CONAGUA/SINAICA no traen cve_mun todavía (alcance de US-105).
-- variacion_matricula excluye el primer ciclo observado de cada cct (no hay "ciclo anterior"
-- real del cual calcular una variación -- mismo principio que target_variacion_matricula en
-- features_escuela: no se rellena con 0 para evitar una fuga de "variación cero" falsa).

with matricula_ciclo as (

    -- NOTA (US-103, Diana): mismo alias que en dim_tiempo.sql/features_escuela --
    -- Data_Model.md documenta `matricula_total`, silver.matricula la entrega como
    -- `alumnos_total`. Pendiente reconciliar el nombre canónico con Deni/Edgar.
    select
        cct,
        ciclo as id_ciclo,
        alumnos_total as matricula_total,
        cast(split_part(ciclo, '-', 1) as int) as anio_inicio
    from {{ source('silver', 'matricula') }}

),

con_anterior as (

    select
        *,
        lag(matricula_total) over (
            partition by cct order by anio_inicio
        ) as matricula_ciclo_anterior
    from matricula_ciclo

),

base as (

    select
        cct,
        id_ciclo,
        matricula_total,
        cast(matricula_total - matricula_ciclo_anterior as double precision)
            as variacion_matricula
    from con_anterior
    where matricula_ciclo_anterior is not null

),

escuela_scope as (

    -- ya viene acotada a SCOPE_ENTIDADES: el join de abajo es lo que restringe el grano
    select cct, cve_mun
    from {{ ref('dim_escuela') }}

),

con_municipio as (

    select
        b.cct,
        b.id_ciclo,
        e.cve_mun,
        b.matricula_total,
        b.variacion_matricula
    from base b
    inner join escuela_scope e on e.cct = b.cct

),

-- D3/D4: infraestructura y conectividad, CEMABE por CCT (ADR-004)
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
            as d3,
        case
            when drenaje_num is not null or electricidad_num is not null
                 or sanitarios_num is not null then 'OK'
            else 'SIN_DATO'
        end as d3_cobertura,
        (coalesce(internet_num, 0) + coalesce(computadoras_num, 0))
            / nullif(
                (case when internet_num is not null then 1 else 0 end)
                + (case when computadoras_num is not null then 1 else 0 end), 0)
            as d4,
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
                then 0.5
            else null
        end as d1,
        r.indice_rezago_social_cobertura as d1_cobertura
    from rezago_ultimo r
    cross join rezago_rango rg
    where r._rn = 1

),

-- D2: inseguridad, SESNSP por municipio. Suma de todos los delitos disponibles (todavía
-- sin alinear meses al ciclo escolar; misma simplificación documentada en features_escuela)
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
        end as d2,
        'OK' as d2_cobertura
    from delitos_por_municipio d
    cross join delitos_rango dr

),

ensamblado as (

    select
        cm.cct,
        cm.id_ciclo,
        cm.cve_mun,
        cm.matricula_total,
        cm.variacion_matricula,
        d1.d1,
        coalesce(d1.d1_cobertura, 'SIN_DATO') as d1_cobertura,
        d2.d2,
        coalesce(d2.d2_cobertura, 'SIN_DATO') as d2_cobertura,
        dd.d3,
        coalesce(dd.d3_cobertura, 'SIN_DATO') as d3_cobertura,
        dd.d4,
        coalesce(dd.d4_cobertura, 'SIN_DATO') as d4_cobertura,
        cast(null as double precision) as d5,
        'SIN_DATO' as d5_cobertura,
        cast(null as double precision) as d6,
        'SIN_DATO' as d6_cobertura
    from con_municipio cm
    left join d3_d4 dd on dd.cct = cm.cct
    left join d1 on d1.cve_mun = cm.cve_mun
    left join d2 on d2.cve_mun = cm.cve_mun

)

select
    cct,
    id_ciclo,
    cve_mun,
    matricula_total,
    variacion_matricula,
    (
        (case when d1_cobertura = 'OK' then 1 else 0 end)
        + (case when d2_cobertura = 'OK' then 1 else 0 end)
        + (case when d3_cobertura = 'OK' then 1 else 0 end)
        + (case when d4_cobertura = 'OK' then 1 else 0 end)
        + (case when d5_cobertura = 'OK' then 1 else 0 end)
        + (case when d6_cobertura = 'OK' then 1 else 0 end)
    ) / 6.0 as indice_completitud_drivers,
    d1,
    d2,
    d3,
    d4,
    d5,
    d6,
    d1_cobertura,
    d2_cobertura,
    d3_cobertura,
    d4_cobertura,
    d5_cobertura,
    d6_cobertura
from ensamblado