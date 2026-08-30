-- =============================================================================
-- db06_cubo_predicciones (virtual)  ·  DB-06 Predicciones
-- -----------------------------------------------------------------------------
-- Historia : US-204  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Cube_Specs_DB06_DB09.md §3
--            KPI-01 matricula, KPI-02 variacion, KPI-05 completitud, KPI-12
--            variacion proyectada (ML-01) + contexto KPI-03/04 (riesgo).
-- Grano    : una fila por cve_mun x nivel x id_ciclo (DEC-009, mismo que
--            gold.cubo_matricula). Cuando C1 cargue el cubo fisico, el dataset
--            se reduce a `SELECT * FROM gold.cubo_matricula` y nada mas se mueve.
--
-- POR QUE COMPONENTES Y NO PROMEDIOS (patron DEC-008, ratificado en DEC-009):
--   La variacion observada, la completitud y la proyeccion ML-01 se guardan
--   como numerador y denominador por separado; la razon vive en
--   metrics_db06_db09.yaml. Asi cualquier combinacion de los filtros globales
--   (AC-002.2) reagrega bien (un promedio de promedios mentiria).
--
-- GRANO DUAL (DEC-010): gold.predicciones puede traer filas de escuela
--   (cct poblado) o de municipio x nivel (sin cct). Aqui se lee SOLO el grano
--   escuela: se une por f.cct = p.cct y se filtra `(p.grano IS NULL OR
--   p.grano = 'escuela')`. Nunca se reparte una proyeccion de municipio a sus
--   escuelas; donde no hay fila de escuela, cobertura_prediccion = 'SIN_DATO'.
--
-- Reglas aplicadas: R1 (ML por LEFT JOIN), R2 (SIN_DATO nunca cero),
--                   R3 (umbral 0.6), R5 (Gold ya viene acotado).
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

    -- ---------- componentes aditivos: observado (KPI-01/02/05) ---------------
    COUNT(DISTINCT f.cct)                       AS escuelas,
    SUM(f.matricula_total)                      AS matricula_total,
    SUM(f.variacion_matricula * f.matricula_total) AS variacion_x_matricula,
    SUM(f.indice_completitud_drivers)           AS suma_completitud,

    -- ---------- componentes aditivos: proyeccion ML-01 (KPI-12) --------------
    -- Lee SOLO el grano escuela de gold.predicciones (DEC-010): el JOIN por
    -- cct impide repartir filas municipio x nivel; el filtro de grano lo hace
    -- explicito y legacy-safe.
    SUM(p.valor)                                AS suma_variacion_proyectada,
    COUNT(p.cct)                                AS escuelas_con_prediccion,

    -- ---------- componentes aditivos: riesgo ML-01 (KPI-03/04) ---------------
    SUM(p.indice_riesgo)                        AS suma_indice_riesgo,
    COUNT(*) FILTER (WHERE p.indice_riesgo >= 0.6) AS escuelas_en_riesgo,  -- R3
    CASE
        WHEN COUNT(p.cct) = 0 THEN 'SIN_DATO'
        ELSE 'OK'
    END                                         AS cobertura_prediccion

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_escuela   e  ON f.cct      = e.cct
JOIN      gold.dim_tiempo    dt ON f.id_ciclo = dt.id_ciclo
JOIN      gold.dim_municipio dm ON f.cve_mun  = dm.cve_mun
LEFT JOIN gold.predicciones  p  ON f.cct      = p.cct
                               AND f.id_ciclo = p.id_ciclo
                               AND p.modelo   = 'ML-01'
                               AND (p.grano IS NULL OR p.grano = 'escuela')
GROUP BY
    f.cve_mun,
    dm.cve_ent,
    dm.nombre_municipio,
    dm.nombre_entidad,
    e.nivel,
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio;