-- =============================================================================
-- gold.cubo_escuela_360  ·  DB-03 Ficha de escuela
-- -----------------------------------------------------------------------------
-- Historia   : US-211a  (Marina Garcia del Buey, Celula 2 - Analytics & BI)
-- Contrato   : 04_UX_Design/Cube_Specs_DB03_DB04.md  (DOC-CUBESPEC-DB0304) §3
-- Grano      : una fila por cct x id_ciclo
-- Uso        : dataset virtual de Superset para DB-03 y, a la vez, SQL de
--              referencia para US-113 (materializacion en dbt, Celula 1).
--
-- Reglas aplicadas:
--   R1  Las salidas de ML se leen por JOIN, nunca como columna del hecho
--       (Data_Model §4.1). LEFT JOIN a proposito: la ficha debe renderizarse
--       aunque el modelo aun no haya puntuado a la escuela (Cube_Specs §2.2).
--   R2  SIN_DATO explicito: nunca cero, nunca nulo silencioso. Prohibido
--       COALESCE(<driver>, 0). Cada driver viaja con su bandera d#_cobertura.
--   R3  Umbral de negocio: escuela en riesgo = indice_riesgo >= 0.6
--       (15_ML_Models/Indice_Riesgo_ML01, ratificado 2026-08-13).
--   R5  Gold ya viene acotado a SCOPE_ENTIDADES; este cubo no repite el filtro.
--
-- Supuesto de unicidad (a confirmar con Celula 3): gold.predicciones es unica
-- por (cct, id_ciclo, modelo) y gold.recomendaciones por (cct, id_ciclo). Si no
-- lo fuera, los LEFT JOIN multiplicarian filas y romperian el grano.
-- =============================================================================

SELECT
    -- ---------- identidad y llaves -------------------------------------------
    f.cct,
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- perfil de la escuela -----------------------------------------
    e.nombre            AS nombre_escuela,
    e.nivel,                                   -- filtro global: nivel educativo
    e.sostenimiento,
    e.latitud,
    e.longitud,
    e.cve_ent,                                 -- filtro global: entidad
    f.cve_mun,                                 -- salto a DB-04
    dm.nombre_municipio,
    dm.nombre_entidad,

    -- ---------- metricas observadas ------------------------------------------
    f.matricula_total,
    f.variacion_matricula,
    f.indice_completitud_drivers,

    -- ---------- los 6 drivers con su bandera de cobertura --------------------
    -- Sin COALESCE: donde no hay dato, el valor queda nulo y la bandera lo dice.
    f.d1, f.d1_cobertura,
    f.d2, f.d2_cobertura,
    f.d3, f.d3_cobertura,
    f.d4, f.d4_cobertura,
    f.d5, f.d5_cobertura,
    f.d6, f.d6_cobertura,

    -- ---------- infraestructura CEMABE (perfil, D3/D4) -----------------------
    -- Se pintan como chips de tres estados: si / no / sin dato.
    e.agua,
    e.drenaje,
    e.electricidad,
    e.sanitarios,
    e.internet,
    e.computadoras,

    -- ---------- salida de ML-01 (prediccion) ---------------------------------
    p.indice_riesgo,
    CASE
        WHEN p.indice_riesgo IS NULL THEN NULL   -- nunca FALSE por ausencia
        ELSE (p.indice_riesgo >= 0.6)            -- R3
    END                 AS en_riesgo,
    p.valor             AS variacion_proyectada,
    p.probabilidad,
    CASE WHEN p.cct IS NULL THEN 'SIN_DATO' ELSE 'OK' END AS cobertura_prediccion,

    -- ---------- salida de ML-02/ML-03 (recomendacion prescriptiva) -----------
    r.driver_dominante,
    dd.nombre           AS nombre_driver,
    r.recomendacion,
    r.prioridad,
    CASE WHEN r.cct IS NULL THEN 'SIN_DATO' ELSE 'OK' END AS cobertura_recomendacion

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_escuela      e  ON f.cct      = e.cct
JOIN      gold.dim_tiempo       dt ON f.id_ciclo = dt.id_ciclo
JOIN      gold.dim_municipio    dm ON f.cve_mun  = dm.cve_mun
LEFT JOIN gold.predicciones     p  ON f.cct      = p.cct
                                  AND f.id_ciclo = p.id_ciclo
                                  AND p.modelo   = 'ML-01'
LEFT JOIN gold.recomendaciones  r  ON f.cct      = r.cct
                                  AND f.id_ciclo = r.id_ciclo
LEFT JOIN gold.dim_driver       dd ON r.driver_dominante = dd.id_driver;
