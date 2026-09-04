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
-- Filtro a nivel de educacion BASICA -- ver CTE `nivel_basica` abajo. El propio contrato del
-- modelo (schema.yml, accepted_values de `nivel`) solo admite PREESCOLAR/PRIMARIA/SECUNDARIA;
-- INICIAL nunca estuvo en su alcance (mismo criterio que NIVELES_BASICA en
-- validacion_formato911_historico.py). Verificado real 2026-09-03 con `dbt show --inline` contra
-- Postgres: cct=11PDI0085S reporta, en los 3 ciclos que rompian los tests (2019-2020,
-- 2023-2024, 2024-2025), turno=1 con nivel=INICIAL y turno=2 con nivel=PREESCOLAR -- la MISMA
-- escuela con un turno de educacion inicial ademas del preescolar, no un choque entre lotes
-- fixture y carga real (esa fue la hipotesis original, descartada con datos reales: el patron se
-- repite identico en los 3 ciclos, incluido el que solo tiene carga real). Sin filtrar, el turno
-- INICIAL sobrevive el dedup por turno y el GROUP BY final parte la escuela en dos filas
-- (INICIAL y PREESCOLAR) para el mismo (cct, ciclo), violando accepted_values de nivel Y
-- unique_matricula_historica_cct_ciclo. Se filtra ANTES del dedup por turno para que la
-- educacion inicial de esa escuela no cuente en matricula_total.
--
-- NOTA: si en el futuro aparece un cct con dos turnos en DOS niveles de la lista basica (p.ej.
-- primaria y secundaria en el mismo plantel), este filtro NO lo resuelve -- unique_cct_ciclo
-- volveria a fallar y habria que decidir con el dueno de Gold como modelar escuelas mixtas.

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

nivel_basica as (

    select *
    from normalizado
    where nivel in ('PREESCOLAR', 'PRIMARIA', 'SECUNDARIA')

),

deduplicado as (

    select *,
        row_number() over (
            partition by cct, ciclo, turno
            order by _ingested_at desc
        ) as _row_number

    from nivel_basica

),

por_turno as (

    select cct, ciclo, cve_ent, cve_mun, nivel, turno, matricula_total, _ingested_at
    from deduplicado
    where _row_number = 1

)

select
    cct,
    ciclo,
    cve_ent,
    cve_mun,
    nivel,
    sum(matricula_total) as matricula_total

from por_turno
group by cct, ciclo, cve_ent, cve_mun, nivel
