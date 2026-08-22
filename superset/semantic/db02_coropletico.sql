-- =============================================================================
-- Coropletico municipal (KPI-10)  ·  DB-02 Mapa de riesgo territorial
-- -----------------------------------------------------------------------------
-- Historia : US-203  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §2 ("coropletico municipal")
-- Grano    : una fila por cve_mun x id_ciclo
--
-- Compone el cubo de riesgo territorial con las geometrias municipales que
-- Superset necesita para deck_polygon: `geometria` viaja como texto GeoJSON
-- (line_type json) y la llave cve_mun (CVEGEO INEGI de 5 digitos) es la misma
-- de gold.dim_municipio y del GeoJSON del asset.
--
-- SIN `nivel` en el grano, A PROPOSITO: con nivel, un municipio produceria una
-- fila por nivel educativo y el JOIN con la geometria dibujaria poligonos
-- superpuestos. El desglose por nivel vive en el cubo territorial y en los
-- puntos de escuela; el color del poligono es siempre municipal.
--
-- gold.geo_municipio es una tabla LOCAL creada por
-- superset/cargar_geojson_municipios.py desde el asset versionado
-- superset/assets/geojson/municipios_scope.geojson (datos publicos INEGI).
--
-- Reglas aplicadas: R1 (ML por JOIN), R2 (SIN_DATO nunca cero: los municipios
--                   sin prediccion se pintan SIN_DATO, no en el color de
--                   riesgo cero), R3 (umbral 0.6).
-- =============================================================================

WITH riesgo AS (
    SELECT
        f.cve_mun,
        dm.cve_ent,
        dm.nombre_municipio,
        dm.nombre_entidad,
        f.id_ciclo,
        dt.ciclo,
        dt.anio_inicio,

        COUNT(DISTINCT f.cct)                          AS escuelas,
        SUM(f.matricula_total)                         AS matricula_total,
        SUM(f.variacion_matricula * f.matricula_total) AS variacion_x_matricula,

        SUM(p.indice_riesgo)                           AS suma_indice_riesgo,
        COUNT(p.cct)                                   AS escuelas_con_prediccion,
        COUNT(*) FILTER (WHERE p.indice_riesgo >= 0.6) AS escuelas_en_riesgo,  -- R3
        CASE
            WHEN COUNT(p.cct) = 0 THEN 'SIN_DATO'
            ELSE 'OK'
        END                                            AS cobertura_riesgo

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
        f.id_ciclo,
        dt.ciclo,
        dt.anio_inicio
)

SELECT
    r.cve_mun,
    r.cve_ent,
    r.nombre_municipio,
    r.nombre_entidad,
    r.id_ciclo,
    r.ciclo,
    r.anio_inicio,
    r.escuelas,
    r.matricula_total,
    r.variacion_x_matricula,
    r.suma_indice_riesgo,
    r.escuelas_con_prediccion,
    r.escuelas_en_riesgo,
    r.cobertura_riesgo,
    g.geometria                                    -- texto GeoJSON para deck_polygon

FROM riesgo r
JOIN gold.geo_municipio g ON r.cve_mun = g.cve_mun
