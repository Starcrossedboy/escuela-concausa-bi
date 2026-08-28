-- =============================================================================
-- db09_cubo_recomendaciones (virtual)  ·  DB-09 Recomendaciones prescriptivas
-- -----------------------------------------------------------------------------
-- Historia : US-204  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Cube_Specs_DB06_DB09.md §5
--            KPI-11 recomendaciones por prioridad, KPI-07 driver dominante,
--            KPI-04 escuelas en riesgo (contexto, AC-002.5) y la tabla
--            "Escuelas a intervenir".
-- Grano    : una fila por cct x id_ciclo. Espejo del cubo fisico
--            gold.cubo_recomendaciones (US-113, C1): misma semantica de
--            cobertura; la columna aditiva `recomendacion_emitida` es el unico
--            0 permitido y su paridad contra gold.recomendaciones la valida C1.
--            Cuando el cubo fisico exista, este dataset se reduce a
--            `SELECT * FROM gold.cubo_recomendaciones` y se le agrega el riesgo
--            por LEFT JOIN a gold.predicciones (contexto de los KPIs globales).
--
-- EL DIFERENCIADOR DEL PROYECTO: la recomendacion prescriptiva de la escuela
--   segun su driver dominante. Una escuela sin recomendacion NO se inventa un
--   driver: `driver_dominante`/`nombre_driver` se etiquetan 'SIN_DATO' como
--   categoria (permitido por R2: etiquetar el vacio, nunca rellenar una
--   metrica con cero) y `cobertura_recomendacion` lo gobierna.
--
-- R1: salidas ML por JOIN (recomendaciones + predicciones, grano escuela DEC-010)
-- R2: SIN_DATO nunca cero. R3: umbral 0.6 para en_riesgo.
-- =============================================================================

SELECT
    -- ---------- identidad ------------------------------------------------------
    f.cct,
    e.nombre                                    AS nombre_escuela,
    e.nivel,                                     -- filtro global: nivel educativo
    e.sostenimiento,

    -- ---------- territorio y tiempo --------------------------------------------
    f.cve_mun,
    dm.cve_ent,                                  -- filtro global: entidad
    dm.nombre_municipio,
    dm.nombre_entidad,
    f.id_ciclo,                                  -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- hechos observados ----------------------------------------------
    f.matricula_total,
    f.indice_completitud_drivers,

    -- ---------- recomendacion prescriptiva (ML-02, por JOIN) -------------------
    COALESCE(r.driver_dominante, 'SIN_DATO')    AS driver_dominante,
    COALESCE(dd.nombre, 'SIN_DATO')             AS nombre_driver,
    r.recomendacion,
    r.prioridad,
    CASE
        WHEN r.cct IS NULL THEN 0
        ELSE 1
    END                                         AS recomendacion_emitida,
    CASE
        WHEN r.cct IS NULL THEN 'SIN_DATO'
        ELSE 'OK'
    END                                         AS cobertura_recomendacion,

    -- ---------- riesgo de contexto (ML-01, por JOIN, grano escuela) ------------
    p.indice_riesgo,
    CASE
        WHEN p.indice_riesgo IS NULL THEN NULL
        WHEN p.indice_riesgo >= 0.6 THEN TRUE      -- R3
        ELSE FALSE
    END                                         AS en_riesgo,
    CASE
        WHEN p.cct IS NULL THEN 'SIN_DATO'
        ELSE 'OK'
    END                                         AS cobertura_prediccion

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_escuela    e  ON f.cct      = e.cct
JOIN      gold.dim_tiempo     dt ON f.id_ciclo = dt.id_ciclo
JOIN      gold.dim_municipio  dm ON f.cve_mun  = dm.cve_mun
LEFT JOIN gold.recomendaciones r ON f.cct      = r.cct
                                AND f.id_ciclo = r.id_ciclo
LEFT JOIN gold.dim_driver     dd ON r.driver_dominante = dd.id_driver
LEFT JOIN gold.predicciones   p  ON f.cct      = p.cct
                                AND f.id_ciclo = p.id_ciclo
                                AND p.modelo   = 'ML-01'
                                AND (p.grano IS NULL OR p.grano = 'escuela')