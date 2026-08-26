-- =============================================================================
-- gold.cubo_comparador_municipio  ·  DB-04 Comparador de municipios
-- -----------------------------------------------------------------------------
-- Historia   : US-211a  (Marina Garcia del Buey, Celula 2 - Analytics & BI)
-- Contrato   : 04_UX_Design/Cube_Specs_DB03_DB04.md  (DOC-CUBESPEC-DB0304) §4
-- Grano      : una fila por cve_mun x nivel x id_ciclo
-- Uso        : dataset virtual de Superset para DB-04 y SQL de referencia para
--              US-113 (materializacion en dbt, Celula 1).
--
-- ATENCION - CAMBIO DE GRANO SOLICITADO A CELULA 1 (Cube_Specs §8.1):
--   Data_Model §4.3 declara el grano municipio x ciclo. Ese grano NO permite
--   cumplir AC-002.2 (filtro global por nivel educativo) en DB-04: si el cubo
--   se pre-agrega sin 'nivel', el filtro no tiene sobre que operar. Se baja el
--   grano a municipio x nivel x ciclo y se reagrega con metricas aditivas.
--   Cambio de esquema => regla 7 del vault: revision humana explicita de Diana.
--
-- POR QUE COMPONENTES Y NO PROMEDIOS:
--   Un promedio no se puede reagregar (el promedio de promedios de tres niveles
--   no es el promedio del municipio). Se guardan numerador y denominador por
--   separado y la razon se calcula en la capa semantica; asi cualquier
--   combinacion de filtros da el numero correcto. Ver metrics_db03_db04.yaml.
--
-- Reglas aplicadas: R1 (ML por JOIN), R2 (SIN_DATO nunca cero),
--                   R3 (umbral 0.6), R5 (Gold ya viene acotado).
-- =============================================================================

SELECT
    -- ---------- identidad y llaves -------------------------------------------
    f.cve_mun,
    dm.cve_ent,                                -- filtro global: entidad
    dm.nombre_municipio,
    dm.nombre_entidad,
    e.nivel,                                   -- filtro global: nivel educativo
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- contexto socioeconomico (KPI-14) -----------------------------
    dm.poblacion,
    dm.pobreza_pct,
    dm.grado_rezago,
    dm.indice_rezago_social,

    -- ---------- componentes aditivos: volumen --------------------------------
    COUNT(DISTINCT f.cct)                       AS escuelas,
    SUM(f.matricula_total)                      AS matricula_total,
    SUM(f.variacion_matricula * f.matricula_total) AS variacion_x_matricula,
    SUM(f.indice_completitud_drivers)           AS suma_completitud,

    -- ---------- componentes aditivos: drivers --------------------------------
    -- Cada driver se suma SOLO sobre las escuelas con cobertura OK y publica su
    -- denominador real. Promediar tratando SIN_DATO como cero afirmaria "aqui no
    -- hay problema" justo donde no se esta midiendo.
    SUM(f.d1) FILTER (WHERE f.d1_cobertura = 'OK')   AS suma_d1,
    COUNT(*)  FILTER (WHERE f.d1_cobertura = 'OK')   AS escuelas_con_d1,
    SUM(f.d2) FILTER (WHERE f.d2_cobertura = 'OK')   AS suma_d2,
    COUNT(*)  FILTER (WHERE f.d2_cobertura = 'OK')   AS escuelas_con_d2,
    SUM(f.d3) FILTER (WHERE f.d3_cobertura = 'OK')   AS suma_d3,
    COUNT(*)  FILTER (WHERE f.d3_cobertura = 'OK')   AS escuelas_con_d3,
    SUM(f.d4) FILTER (WHERE f.d4_cobertura = 'OK')   AS suma_d4,
    COUNT(*)  FILTER (WHERE f.d4_cobertura = 'OK')   AS escuelas_con_d4,
    SUM(f.d5) FILTER (WHERE f.d5_cobertura = 'OK')   AS suma_d5,
    COUNT(*)  FILTER (WHERE f.d5_cobertura = 'OK')   AS escuelas_con_d5,
    SUM(f.d6) FILTER (WHERE f.d6_cobertura = 'OK')   AS suma_d6,
    COUNT(*)  FILTER (WHERE f.d6_cobertura = 'OK')   AS escuelas_con_d6,

    -- ---------- componentes aditivos: riesgo (ML-01) -------------------------
    SUM(p.indice_riesgo)                        AS suma_indice_riesgo,
    COUNT(p.cct)                                AS escuelas_con_prediccion,
    COUNT(*) FILTER (WHERE p.indice_riesgo >= 0.6) AS escuelas_en_riesgo,  -- R3
    CASE
        WHEN COUNT(p.cct) = 0 THEN 'SIN_DATO'
        ELSE 'OK'
    END                                         AS cobertura_riesgo

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_escuela   e  ON f.cct      = e.cct
JOIN      gold.dim_tiempo    dt ON f.id_ciclo = dt.id_ciclo
JOIN      gold.dim_municipio dm ON f.cve_mun  = dm.cve_mun
LEFT JOIN gold.predicciones  p  ON f.cct      = p.cct
                               AND f.id_ciclo = p.id_ciclo
                               AND p.modelo   = 'ML-01'
GROUP BY
    f.cve_mun,
    dm.cve_ent,
    dm.nombre_municipio,
    dm.nombre_entidad,
    e.nivel,
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio,
    dm.poblacion,
    dm.pobreza_pct,
    dm.grado_rezago,
    dm.indice_rezago_social;
