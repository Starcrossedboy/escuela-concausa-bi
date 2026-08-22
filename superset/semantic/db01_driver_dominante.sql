-- =============================================================================
-- Driver dominante (KPI-07)  ·  DB-01 Ejecutivo
-- -----------------------------------------------------------------------------
-- Historia : US-203  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §4 (KPI-07)
-- Grano    : una fila por driver_dominante x id_ciclo
--
-- ML POR JOIN (R1, Data_Model §4.1): driver_dominante vive en gold.recomendaciones
--   (salida de ML-02) y se consulta por JOIN (cct, id_ciclo). LEFT JOIN: mientras
--   ML-02 no haya puntuado a todas las escuelas, el resto del sistema no aparece
--   como "sin explicacion" fantasma; se agrupa bajo la etiqueta SIN_DATO.
--
-- Nota R2: el COALESCE de abajo etiqueta una CATEGORIA vacia ('SIN_DATO'), no
--   rellena una metrica con cero. Las escuelas sin recomendacion se cuentan como
--   tales, nunca desaparecen ni se reparten entre drivers reales.
-- =============================================================================

SELECT
    COALESCE(dd.id_driver, 'SIN_DATO')          AS id_driver,
    COALESCE(dd.nombre, 'Sin recomendacion')     AS nombre_driver,
    f.id_ciclo,                                  -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    COUNT(DISTINCT f.cct)                        AS escuelas

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_tiempo       dt ON f.id_ciclo = dt.id_ciclo
LEFT JOIN gold.recomendaciones r  ON f.cct            = r.cct
                                 AND f.id_ciclo        = r.id_ciclo
LEFT JOIN gold.dim_driver       dd ON r.driver_dominante = dd.id_driver
GROUP BY
    dd.id_driver,
    dd.nombre,
    f.id_ciclo,
    dt.ciclo,
    dt.anio_inicio
