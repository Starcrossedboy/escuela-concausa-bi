-- gold.dim_municipio (US-103) — Data_Model.md §4.2/§6. PK: cve_mun. Acotado a
-- SCOPE_ENTIDADES (Data_Model.md §7): CDMX, Edomex, Nuevo León, Jalisco.
--
-- cve_ent se deriva de los primeros 2 caracteres de cve_mun (homologación INEGI, siempre
-- correcta por construcción: cve_mun = cve_ent(2) + cve_mun_local(3)), en vez de depender de
-- que silver.poblacion_municipio o silver.rezago_municipio la traigan completa.
--
-- NOTA: Data_Model.md §6 documenta nombre_municipio/nombre_entidad como originadas en DS-07,
-- pero silver.rezago_municipio (US-111, Deni) las expone como `entidad`/`municipio` a secas
-- (mismo patrón de nombres-no-reconciliados que ciclo/id_ciclo y matricula_total/alumnos_total
-- en US-103/US-104). Se aliasean aquí; pendiente reconciliar el nombre canónico con Deni/Edgar.

with poblacion_por_municipio as (

    select
        cve_mun,
        max(anio) over (partition by cve_mun) as anio_max,
        anio,
        sum(poblacion) as poblacion_anio
    from {{ ref('poblacion_municipio') }}
    group by cve_mun, anio

),

poblacion as (

    select cve_mun, poblacion_anio as poblacion
    from poblacion_por_municipio
    where anio = anio_max

),

rezago_ultimo as (

    select
        cve_mun,
        entidad as nombre_entidad,
        municipio as nombre_municipio,
        indice_rezago_social,
        indice_rezago_social_cobertura,
        grado_rezago,
        pobreza_pct,
        row_number() over (
            partition by cve_mun order by periodo_medicion desc
        ) as _rn
    from {{ ref('rezago_municipio') }}

)

select
    r.cve_mun,
    substring(r.cve_mun, 1, 2) as cve_ent,
    r.nombre_municipio,
    r.nombre_entidad,
    p.poblacion,
    case when r.indice_rezago_social_cobertura = 'OK' then r.indice_rezago_social end
        as indice_rezago_social,
    r.grado_rezago,
    r.pobreza_pct
from rezago_ultimo r
left join poblacion p on p.cve_mun = r.cve_mun
where r._rn = 1
  and substring(r.cve_mun, 1, 2) in {{ scope_entidades() }}