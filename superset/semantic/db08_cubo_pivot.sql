-- =============================================================================
-- gold.cubo_pivot  ·  DB-08 Explorador del cubo
-- -----------------------------------------------------------------------------
-- Historia   : US-211b  (Monserrat Xcaret Miranda Olivas, Celula 2 - Analytics & BI)
-- Contrato   : 04_UX_Design/Cube_Specs_DB05_DB08.md  (DOC-CUBESPEC-DB0508) §4
-- Grano      : una fila por cct x id_driver x id_ciclo
-- Uso        : dataset virtual de Superset para DB-08 y SQL de referencia para
--              US-113 (materializacion en dbt, Celula 1).
--
-- SIN cambio de grano: coincide 1:1 con Data_Model §4.3 (cct x driver x ciclo).
--   'nivel' viaja gratis como atributo de dim_escuela via cct, igual que en
--   db03_cubo_escuela_360.sql -- por eso este cubo NO necesita la solicitud de
--   cambio de grano que si aplica a db05_cubo_driver.sql (ver Cube_Specs §8.2).
--
-- FORMATO LARGO (unpivot): una fila por driver, no columnas d1..d6 (mismo
--   criterio que db05_cubo_driver.sql, Cube_Specs §2.2).
--   ADVERTENCIA - DOBLE CONTEO: 'matricula_total' e 'indice_completitud_drivers'
--   se repiten x6 (una vez por id_driver) para la misma escuela x ciclo. No
--   sumar sin agrupar/filtrar por id_driver.
--
-- v1 NO usa LEFT JOIN a salidas de ML (Cube_Specs §2.1): analiza el driver
--   OBSERVADO, no la prediccion. Fuera de alcance v1: banderas CEMABE crudas
--   e indice_riesgo/recomendacion (Cube_Specs §4.2).
--
-- Grano de detalle: AVG() es seguro en la capa semantica para 'valor_driver'
--   (no es promedio de promedios) y excluye NULL de forma nativa -- mismo
--   efecto que filtrar por cobertura_driver = 'OK' (Cube_Specs §4.3).
--
-- Reglas aplicadas: R2 (SIN_DATO nunca cero -- sin COALESCE(d#, 0)),
--   R5 (Gold ya viene acotado). R1/R3 no aplican a v1.
-- Sin GROUP BY: se esta al grano del hecho, igual que db03_cubo_escuela_360.sql
-- =============================================================================

WITH escuela_driver AS (
    SELECT f.cct, f.cve_mun, f.id_ciclo, f.matricula_total, f.indice_completitud_drivers,
           'D1' AS id_driver, f.d1 AS valor_driver, f.d1_cobertura AS cobertura_driver
    FROM gold.fact_escuela_ciclo f

    UNION ALL

    SELECT f.cct, f.cve_mun, f.id_ciclo, f.matricula_total, f.indice_completitud_drivers,
           'D2' AS id_driver, f.d2 AS valor_driver, f.d2_cobertura AS cobertura_driver
    FROM gold.fact_escuela_ciclo f

    UNION ALL

    SELECT f.cct, f.cve_mun, f.id_ciclo, f.matricula_total, f.indice_completitud_drivers,
           'D3' AS id_driver, f.d3 AS valor_driver, f.d3_cobertura AS cobertura_driver
    FROM gold.fact_escuela_ciclo f

    UNION ALL

    SELECT f.cct, f.cve_mun, f.id_ciclo, f.matricula_total, f.indice_completitud_drivers,
           'D4' AS id_driver, f.d4 AS valor_driver, f.d4_cobertura AS cobertura_driver
    FROM gold.fact_escuela_ciclo f

    UNION ALL

    SELECT f.cct, f.cve_mun, f.id_ciclo, f.matricula_total, f.indice_completitud_drivers,
           'D5' AS id_driver, f.d5 AS valor_driver, f.d5_cobertura AS cobertura_driver
    FROM gold.fact_escuela_ciclo f

    UNION ALL

    SELECT f.cct, f.cve_mun, f.id_ciclo, f.matricula_total, f.indice_completitud_drivers,
           'D6' AS id_driver, f.d6 AS valor_driver, f.d6_cobertura AS cobertura_driver
    FROM gold.fact_escuela_ciclo f
)
SELECT
    -- ---------- identidad y llaves ---------------------------------------------
    ed.cct,
    e.nombre             AS nombre_escuela,
    e.nivel,                                   -- filtro global: nivel educativo
    e.sostenimiento,
    e.cve_ent,                                 -- filtro global: entidad
    ed.cve_mun,
    dm.nombre_municipio,
    dm.nombre_entidad,
    ed.id_ciclo,                               -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- identidad del driver -------------------------------------------
    ed.id_driver,
    dd.nombre            AS nombre_driver,
    dd.fuente            AS fuente_driver,
    dd.nivel_geografico  AS driver_nivel_geografico,

    -- ---------- valor y cobertura -----------------------------------------------
    ed.valor_driver,
    ed.cobertura_driver,

    -- ---------- contexto (repetido x6, ver ADVERTENCIA arriba) -------------------
    ed.matricula_total,
    ed.indice_completitud_drivers

FROM escuela_driver ed
JOIN gold.dim_escuela   e  ON ed.cct     = e.cct
JOIN gold.dim_municipio dm ON ed.cve_mun = dm.cve_mun
JOIN gold.dim_tiempo    dt ON ed.id_ciclo = dt.id_ciclo
JOIN gold.dim_driver    dd ON ed.id_driver = dd.id_driver;
