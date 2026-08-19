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
--   D5 agua              -- SIN_DATO explícito: DS-06 CONAGUA (dueño Emilio Galnares Ruiz)
--                            todavía no tiene su "prueba de descarga real" completa, no hay
--                            bronze.conagua con datos todavía
--   D6 aire              -- real (2026-08-19, ADR-006, US-105): interpolación IDW de
--                            silver.aire_estacion (SINAICA) hacia cada escuela georreferenciada
--                            de dim_escuela. Radio válido 15km, potencia 2; fuera de radio ->
--                            SIN_DATO explícito
--
-- D5 en SIN_DATO no es un hueco escondido: es la regla del proyecto (Data_Model.md §3,
-- "SIN_DATO explícito, nunca cero ni nulo silencioso") aplicada honestamente a una fuente que
-- todavía no tiene datos reales. Cuando DS-06 entregue su prueba de descarga, se replica aquí
-- el mismo patrón IDW que ya tiene D6.
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

-- D6: calidad del aire, SINAICA, interpolación IDW hacia cada escuela (ADR-006, US-105).
-- Mismo enfoque que gold.fact_escuela_ciclo: radio válido 15km, potencia 2 (IDW estándar);
-- fuera de radio -> SIN_DATO explícito. Solo usa lecturas de PM2.5 (contaminante criterio
-- más reportado por SINAICA, ver DS-05.md §5) marcadas válidas por la propia API.
aire_pm25 as (

    select
        id_estacion,
        max(latitud) as latitud,
        max(longitud) as longitud,
        avg(valor) as pm25_promedio
    from {{ source('silver', 'aire_estacion') }}
    where parametro = 'PM2.5' and dato_valido = 1
        and latitud is not null and longitud is not null
    group by id_estacion

),

escuela_geo as (

    select cct, latitud, longitud
    from {{ ref('dim_escuela') }}
    where latitud is not null and longitud is not null

),

distancias_aire as (

    select
        e.cct,
        a.pm25_promedio,
        6371 * acos(least(1.0, greatest(-1.0,
            cos(radians(e.latitud)) * cos(radians(a.latitud))
                * cos(radians(a.longitud) - radians(e.longitud))
            + sin(radians(e.latitud)) * sin(radians(a.latitud))
        ))) as distancia_km
    from escuela_geo e
    cross join aire_pm25 a

),

dentro_radio_aire as (

    select
        cct,
        pm25_promedio,
        distancia_km,
        greatest(distancia_km, 0.001) as distancia_km_adj
    from distancias_aire
    where distancia_km <= 15

),

d6_interpolado as (

    select
        cct,
        sum(pm25_promedio / power(distancia_km_adj, 2)) / sum(1.0 / power(distancia_km_adj, 2))
            as d6_valor,
        min(distancia_km) as distancia_min_km
    from dentro_radio_aire
    group by cct

),

d6_rango as (

    select min(d6_valor) as min_val, max(d6_valor) as max_val
    from d6_interpolado

),

d6 as (

    select
        i.cct,
        case
            when rg.max_val > rg.min_val then (i.d6_valor - rg.min_val) / (rg.max_val - rg.min_val)
            else 0.5
        end as d6_aire,
        'OK' as d6_cobertura
    from d6_interpolado i
    cross join d6_rango rg

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
        d6.d6_aire,
        coalesce(d6.d6_cobertura, 'SIN_DATO') as d6_cobertura,
        b.target_variacion_matricula
    from base b
    left join d3_d4 dd on dd.cct = b.cct
    left join d1 on d1.cve_mun = b.cve_mun
    left join d2 on d2.cve_mun = b.cve_mun
    left join d6 on d6.cct = b.cct

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