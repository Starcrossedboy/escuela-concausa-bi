-- =============================================================================
-- gold.cubo_driver  ·  DB-05 Análisis por driver
-- -----------------------------------------------------------------------------
-- Historia   : US-211b  (Monserrat Xcaret Miranda Olivas, Celula 2 - Analytics & BI)
-- Contrato   : 04_UX_Design/Cube_Specs_DB05_DB08.md  (DOC-CUBESPEC-DB0508) §3
-- Grano      : una fila por id_driver x cve_mun x nivel x id_ciclo
-- Uso        : dataset virtual de Superset para DB-05 y SQL de referencia para
--              US-113 (materializacion en dbt, Celula 1).
--
-- CAMBIO DE GRANO ACEPTADO POR CELULA 1 -- DEC-009, 2026-08-22 (Cube_Specs §8.1):
--   Data_Model §4.3 declaraba el grano driver x municipio x ciclo. Ese grano NO
--   permitia cumplir AC-002.2 (filtro global por nivel educativo) en DB-05: si
--   el cubo se pre-agrega sin 'nivel', el filtro no tiene sobre que operar. Se
--   baja el grano a driver x municipio x nivel x ciclo y se reagrega con
--   metricas aditivas. Cambio de esquema => regla 7 del vault: revision
--   humana explicita de Diana. No bloquea: este SQL ya trae el grano
--   propuesto (precedente identico: DEC-008, 2026-08-14, para cubo_driver
--   "hermano" gold.cubo_comparador_municipio).
--
-- FORMATO LARGO (unpivot): una fila por driver, no columnas d1..d6. Mismo
--   patron que ya usa KPI-06 de Screen_Specs. Permite que DB-05 muestre "un
--   tab por driver" (US-213) con un solo juego de charts filtrado por
--   id_driver, en vez de 6 charts casi duplicados por columna.
--   ADVERTENCIA - DOBLE CONTEO: 'escuelas' y 'suma_valor' se repiten x6 (una
--   vez por id_driver) dentro del mismo municipio x nivel x ciclo. Sumarlas
--   sin agrupar/filtrar por id_driver las infla x6. Ver Cube_Specs §2.2/§3.6
--   y metrics_db05_db08.yaml (dimension_obligatoria_en_agregacion: id_driver).
--
-- v1 NO usa LEFT JOIN a salidas de ML (Cube_Specs §2.1): este cubo analiza el
--   driver OBSERVADO (d1..d6 de fact_escuela_ciclo), no la prediccion.
--
-- POR QUE COMPONENTES Y NO PROMEDIOS: igual razon que db04_cubo_comparador_
--   municipio.sql -- un promedio no se puede reagregar. Se guardan numerador
--   (suma_valor) y denominador (escuelas_con_dato) por separado; la razon se
--   calcula en la capa semantica (metrics_db05_db08.yaml).
--
-- Reglas aplicadas: R2 (SIN_DATO nunca cero), R5 (Gold ya viene acotado).
--   R1/R3 no aplican a v1 (no hay salida de ML en este cubo).
-- =============================================================================

WITH escuela_driver AS (
    SELECT f.cct, f.cve_mun, e.cve_ent, e.nivel, f.id_ciclo,
           'D1' AS id_driver, f.d1 AS valor, f.d1_cobertura AS cobertura
    FROM gold.fact_escuela_ciclo f
    JOIN gold.dim_escuela e ON f.cct = e.cct

    UNION ALL

    SELECT f.cct, f.cve_mun, e.cve_ent, e.nivel, f.id_ciclo,
           'D2' AS id_driver, f.d2 AS valor, f.d2_cobertura AS cobertura
    FROM gold.fact_escuela_ciclo f
    JOIN gold.dim_escuela e ON f.cct = e.cct

    UNION ALL

    SELECT f.cct, f.cve_mun, e.cve_ent, e.nivel, f.id_ciclo,
           'D3' AS id_driver, f.d3 AS valor, f.d3_cobertura AS cobertura
    FROM gold.fact_escuela_ciclo f
    JOIN gold.dim_escuela e ON f.cct = e.cct

    UNION ALL

    SELECT f.cct, f.cve_mun, e.cve_ent, e.nivel, f.id_ciclo,
           'D4' AS id_driver, f.d4 AS valor, f.d4_cobertura AS cobertura
    FROM gold.fact_escuela_ciclo f
    JOIN gold.dim_escuela e ON f.cct = e.cct

    UNION ALL

    SELECT f.cct, f.cve_mun, e.cve_ent, e.nivel, f.id_ciclo,
           'D5' AS id_driver, f.d5 AS valor, f.d5_cobertura AS cobertura
    FROM gold.fact_escuela_ciclo f
    JOIN gold.dim_escuela e ON f.cct = e.cct

    UNION ALL

    SELECT f.cct, f.cve_mun, e.cve_ent, e.nivel, f.id_ciclo,
           'D6' AS id_driver, f.d6 AS valor, f.d6_cobertura AS cobertura
    FROM gold.fact_escuela_ciclo f
    JOIN gold.dim_escuela e ON f.cct = e.cct
),
agregado AS (
    SELECT
        ed.id_driver,
        ed.cve_mun,
        ed.cve_ent,
        ed.nivel,
        ed.id_ciclo,

        COUNT(DISTINCT ed.cct)                          AS escuelas,
        SUM(ed.valor) FILTER (WHERE ed.cobertura = 'OK') AS suma_valor,
        COUNT(*)      FILTER (WHERE ed.cobertura = 'OK') AS escuelas_con_dato,
        CASE
            WHEN COUNT(*) FILTER (WHERE ed.cobertura = 'OK') = 0 THEN 'SIN_DATO'
            ELSE 'OK'
        END                                              AS cobertura_driver

    FROM escuela_driver ed
    GROUP BY ed.id_driver, ed.cve_mun, ed.cve_ent, ed.nivel, ed.id_ciclo
)
SELECT
    -- ---------- identidad del driver ------------------------------------------
    a.id_driver,                               -- filtro/selector: tab del driver
    dd.nombre           AS nombre_driver,
    dd.fuente           AS fuente_driver,
    dd.nivel_geografico AS driver_nivel_geografico,

    -- ---------- identidad y llaves geograficas --------------------------------
    a.cve_mun,
    a.cve_ent,                                 -- filtro global: entidad
    dm.nombre_municipio,
    dm.nombre_entidad,
    a.nivel,                                   -- filtro global: nivel educativo
    a.id_ciclo,                                -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- componentes aditivos (ver ADVERTENCIA de doble conteo arriba) -
    a.escuelas,
    a.suma_valor,
    a.escuelas_con_dato,
    a.cobertura_driver

FROM agregado a
JOIN gold.dim_driver    dd ON a.id_driver = dd.id_driver
JOIN gold.dim_municipio dm ON a.cve_mun   = dm.cve_mun
JOIN gold.dim_tiempo    dt ON a.id_ciclo  = dt.id_ciclo;
