-- silver.matricula_historica (DS-01, distribucion HISTORICA multi-ciclo) -- mitigacion de
-- RISK-007/DEC-007. AISLADO de silver.matricula (ciclo unico 2024-2025) -- ver
-- src/ingesta/extractor_formato911_historico.py y bronze.formato911_historico.
--
-- Grano de bronze: cct x ciclo x turno. insc_t es matricula POR TURNO, no por escuela --
-- confirmado con datos reales del ciclo 2024-2025 (3,388 cct con >1 turno y valores de insc_t
-- distintos entre turnos, ver DevLog 2026-08-21). Por eso aqui se SUMA por turno para obtener
-- la matricula total real de la escuela en el ciclo.
--
-- nivel se normaliza a MAYUSCULAS (UPPER(TRIM())) para hacer match con gold.dim_escuela.nivel
-- (DS-02), que no se homologa en su propio modelo Silver -- ver silver/escuela.sql.
--
-- Se deja la columna como `ciclo` (no `id_ciclo`): mismo nombre que ya expone silver.matricula
-- hoy (ver nota en dim_tiempo.sql sobre esta ambiguedad pendiente de reconciliar). El cambio a
-- `id_ciclo` que exige unir_target() se hace en Gold, igual que ya hace dim_tiempo.sql.
--
-- Segundo dedup, a grano (cct, ciclo) -- ver CTE `lote_mas_reciente` abajo. Bronze es
-- append-only (CLAUDE.md: nunca DELETE/UPDATE/DROP desde el agente): filas fixture viejas
-- (p.ej. BUG-026) conviven con la carga real para el mismo cct+ciclo. El primer dedup (por
-- turno) no las toca si su `turno` no aparece en la carga real -- y si su `cve_mun`/`nivel`
-- difieren de la carga real, el GROUP BY final las partia en dos filas para el mismo
-- (cct, ciclo), violando unique_matricula_historica_cct_ciclo (y a veces tambien
-- accepted_values de nivel, si el valor fixture no es PREESCOLAR/PRIMARIA/SECUNDARIA).
-- Verificado real 2026-09-03: 6 filas fixture con cct que coincide con el catalogo real de
-- DS-02 causaban exactamente esto. Fix: por cct+ciclo, quedarse solo con las filas del LOTE
-- mas reciente (max _ingested_at) -- cada corrida de carga real escribe un _ingested_at
-- propio para todas sus filas (ver cargar_bronze_formato911_historico_real.py), asi que un
-- lote fixture viejo nunca gana contra uno real mas nuevo.

with normalizado as (

    select
        cct,
        ciclo,
        turno,
        {{ normalize_cve_ent('entidad') }} as cve_ent,
        {{ normalize_cve_mun('entidad', 'municipio') }} as cve_mun,
        upper(trim(nivel)) as nivel,
        matricula_total,
        _ingested_at

    from {{ source('bronze', 'formato911_historico') }}

),

deduplicado as (

    select *,
        row_number() over (
            partition by cct, ciclo, turno
            order by _ingested_at desc
        ) as _row_number

    from normalizado

),

por_turno as (

    select cct, ciclo, cve_ent, cve_mun, nivel, turno, matricula_total, _ingested_at
    from deduplicado
    where _row_number = 1

),

lote_mas_reciente as (

    select cct, ciclo, max(_ingested_at) as _ingested_at_lote
    from por_turno
    group by cct, ciclo

),

del_lote_vigente as (

    select pt.cct, pt.ciclo, pt.cve_ent, pt.cve_mun, pt.nivel, pt.matricula_total
    from por_turno as pt
    inner join lote_mas_reciente as lr
        on pt.cct = lr.cct
        and pt.ciclo = lr.ciclo
        and pt._ingested_at = lr._ingested_at_lote

)

select
    cct,
    ciclo,
    cve_ent,
    cve_mun,
    nivel,
    sum(matricula_total) as matricula_total

from del_lote_vigente
group by cct, ciclo, cve_ent, cve_mun, nivel