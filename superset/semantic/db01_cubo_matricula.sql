-- =============================================================================
-- gold.cubo_matricula (virtual)  ·  DB-01 Ejecutivo
-- -----------------------------------------------------------------------------
-- Historia   : US-203  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato   : 04_UX_Design/Screen_Specs.md §2 (cubo de DB-01) y §4 (KPI-01/02/05)
-- Grano      : una fila por cve_mun x nivel x id_ciclo
-- Uso        : dataset virtual de Superset para DB-01 y SQL de referencia para
--              US-113 (materializacion en dbt, Celula 1). Cuando el cubo real
--              exista, este dataset cambia su SQL por `SELECT * FROM
--              gold.cubo_matricula` y nada mas se mueve.
--
-- POR QUE COMPONENTES Y NO PROMEDIOS (patron DEC-008, ratificado para DB-04):
--   La variacion ponderada y la completitud se guardan como numerador y
--   denominador por separado; la razon vive en metrics_db01_db02.yaml. Asi
--   cualquier combinacion de los filtros globales (AC-002.2) reagrega bien.
--
-- Reglas aplicadas: R1 (hechos observados: aqui NO hay salidas de ML),
--                   R2 (SIN_DATO nunca cero: sin COALESCE a 0),
--                   R5 (Gold ya viene acotado a SCOPE_ENTIDADES).
-- =============================================================================

SELECT
    -- ---------- identidad y llaves -------------------------------------------
    f.cve_mun,
    dm.cve_ent,                                -- filtro global: entidad
    dm.nombre_municipio,
    dm.nombre_entidad,
    e.nivel,                                   -- filtro global: nivel educativo
    f.id_ciclo,                                -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- componentes aditivos -----------------------------------------
    COUNT(DISTINCT f.cct)                          AS escuelas,
    SUM(f.matricula_total)                         AS matricula_total,
    SUM(f.variacion_matricula * f.matricula_total) AS variacion_x_matricula,
    SUM(f.indice_completitud_drivers)              AS suma_completitud

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_escuela   e  ON f.cct      = e.cct
JOIN      gold.dim_tiempo    dt ON f.id_ciclo = dt.id_ciclo
JOIN      gold.dim_municipio dm ON f.cve_mun  = dm.cve_mun
GROUP BY
    f.cve_mun,
    dm.cve_ent,
    dm.nombre_municipio,
    dm.nombre_entidad,
    e.nivel,
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio
