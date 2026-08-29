-- =============================================================================
-- Mapa de vacíos (KPI-06, agregado municipal)  ·  DB-07 Calidad y cobertura
-- -----------------------------------------------------------------------------
-- Historia : US-222 (Oscar Antonio Quiroz Lázaro, Célula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §4 (KPI-06)
-- Grano    : cve_mun × id_ciclo (agregado, sin nivel ni driver)
--
-- SIN nivel ni id_driver en el grano, A PROPÓSITO (mismo patrón que
-- db02_coropletico.sql): con esas dimensiones, un municipio produciría
-- varias filas y el JOIN con la geometría dibujaría polígonos superpuestos.
-- El desglose por nivel/driver vive en db07_cubo_completitud; el color del
-- polígono aquí es siempre el vacío total municipal, sumando los 6 drivers.
--
-- gold.geo_municipio es la tabla LOCAL creada por
-- superset/cargar_geojson_municipios.py (mismo patrón que DB-02).
-- =============================================================================
WITH completitud AS (
    SELECT
        cve_mun,
        cve_ent,
        nombre_municipio,
        nombre_entidad,
        id_ciclo,
        ciclo,
        anio_inicio,
        SUM(total_escuelas)    AS total_escuelas,
        SUM(escuelas_con_dato) AS escuelas_con_dato,
        SUM(escuelas_sin_dato) AS escuelas_sin_dato,
        SUM(suma_completitud)  AS suma_completitud
    FROM gold.cubo_completitud
    GROUP BY cve_mun, cve_ent, nombre_municipio, nombre_entidad, id_ciclo, ciclo, anio_inicio
)
SELECT
    c.cve_mun,
    c.cve_ent,
    COALESCE(g.nombre_municipio, c.nombre_municipio) AS nombre_municipio,
    c.nombre_entidad,
    c.id_ciclo,
    c.ciclo,
    c.anio_inicio,
    c.total_escuelas,
    c.escuelas_con_dato,
    c.escuelas_sin_dato,
    c.suma_completitud,
    g.geometria
FROM completitud c
JOIN gold.geo_municipio g ON c.cve_mun = g.cve_mun