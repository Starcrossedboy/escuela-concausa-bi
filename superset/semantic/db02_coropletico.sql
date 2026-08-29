-- =============================================================================
-- db02_coropletico  ·  DB-02 Mapa de riesgo territorial (KPI-10)
-- -----------------------------------------------------------------------------
-- Historia : US-205  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §2 ("coropletico municipal")
-- Grano    : una fila por cve_mun x id_ciclo
--
-- REPUNTEO A CUBOS FISICOS (US-205 / US-113): REAGREGA gold.cubo_riesgo_
--   territorial (grano cve_mun x nivel x ciclo) al grano municipal del
--   coropletico (cve_mun x ciclo) SUMANDO los componentes aditivos y las
--   geometrias municipales que Superset necesita para deck_polygon: `geometria`
--   viaja como texto GeoJSON (line_type json) y la llave cve_mun (CVEGEO INEGI
--   de 5 digitos) es la misma de dim_municipio y del GeoJSON del asset.
--
-- SIN `nivel` en el grano, A PROPOSITO: con nivel, un municipio produciria una
--   fila por nivel educativo y el JOIN con la geometria dibujaria poligonos
--   superpuestos. El desglose por nivel vive en el cubo territorial y en los
--   puntos de escuela; el color del poligono es siempre municipal.
--
-- La cobertura se RE-computa en la reagregacion: si entre los niveles del
--   municipio nadie fue puntuado, el poligono se pinta 'SIN_DATO', nunca en el
--   color de riesgo cero (R2).
--
-- gold.geo_municipio es una tabla LOCAL creada por
--   superset/cargar_geojson_municipios.py desde el asset versionado
--   superset/assets/geojson/municipios_scope.geojson (datos publicos INEGI).
--
-- Reglas aplicadas: R2 (SIN_DATO nunca cero), R5 (Gold ya viene acotado).
--   R1/R3 viven en el cubo C1.
-- =============================================================================

WITH riesgo AS (
    SELECT
        rt.cve_mun,
        rt.cve_ent,
        rt.nombre_municipio,
        rt.nombre_entidad,
        rt.id_ciclo,
        rt.ciclo,
        rt.anio_inicio,

        SUM(rt.escuelas)                    AS escuelas,
        SUM(rt.matricula_total)             AS matricula_total,
        SUM(rt.variacion_x_matricula)       AS variacion_x_matricula,

        SUM(rt.suma_indice_riesgo)          AS suma_indice_riesgo,
        SUM(rt.escuelas_con_prediccion)     AS escuelas_con_prediccion,
        SUM(rt.escuelas_en_riesgo)          AS escuelas_en_riesgo,
        CASE
            WHEN SUM(rt.escuelas_con_prediccion) = 0 THEN 'SIN_DATO'
            ELSE 'OK'
        END                                 AS cobertura_riesgo
    FROM gold.cubo_riesgo_territorial rt
    GROUP BY
        rt.cve_mun,
        rt.cve_ent,
        rt.nombre_municipio,
        rt.nombre_entidad,
        rt.id_ciclo,
        rt.ciclo,
        rt.anio_inicio
)

SELECT
    r.cve_mun,
    r.cve_ent,
    COALESCE(g.nombre_municipio, r.nombre_municipio) AS nombre_municipio,
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