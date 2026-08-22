-- =============================================================================
-- Puntos de escuela georreferenciados  ·  DB-02 Mapa de riesgo territorial
-- -----------------------------------------------------------------------------
-- Historia : US-203  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §2 ("coropletico municipal + puntos de
--            escuela por indice de riesgo")
-- Grano    : una fila por cct x id_ciclo (grano del hecho, sin agregar)
--
-- Capa de puntos del mapa: cada escuela con latitud/longitud y su riesgo si ML-01
-- ya la puntuo. R1: indice_riesgo por LEFT JOIN a gold.predicciones filtrando
-- modelo = 'ML-01' con la llave completa (cct, id_ciclo). Una escuela sin
-- prediccion NO desaparece del mapa: viaja con cobertura_prediccion = 'SIN_DATO'
-- y en_riesgo nulo (desconocido, no falso).
--
-- Reglas aplicadas: R1 (ML por JOIN), R2 (SIN_DATO nunca cero), R3 (umbral 0.6).
-- =============================================================================

SELECT
    -- ---------- identidad ------------------------------------------------------
    f.cct,
    e.nombre,
    e.nivel,                                     -- filtro global: nivel educativo
    e.sostenimiento,

    -- ---------- georreferencia -------------------------------------------------
    e.latitud,
    e.longitud,

    -- ---------- territorio y tiempo --------------------------------------------
    f.cve_mun,
    dm.cve_ent,                                  -- filtro global: entidad
    COALESCE(g.nombre_municipio, dm.nombre_municipio) AS nombre_municipio,
    dm.nombre_entidad,
    f.id_ciclo,                                  -- filtro global: ciclo
    dt.ciclo,
    dt.anio_inicio,

    -- ---------- hechos observados ----------------------------------------------
    f.matricula_total,
    f.variacion_matricula,

    -- ---------- riesgo (ML-01, por JOIN) ---------------------------------------
    p.indice_riesgo,
    CASE
        WHEN p.indice_riesgo IS NULL THEN NULL
        WHEN p.indice_riesgo >= 0.6 THEN TRUE      -- R3
        ELSE FALSE
    END                                          AS en_riesgo,
    CASE
        WHEN p.cct IS NULL THEN 'SIN_DATO'
        ELSE 'OK'
    END                                          AS cobertura_prediccion

FROM gold.fact_escuela_ciclo f
JOIN      gold.dim_escuela   e  ON f.cct      = e.cct
JOIN      gold.dim_tiempo    dt ON f.id_ciclo = dt.id_ciclo
JOIN      gold.dim_municipio dm ON f.cve_mun  = dm.cve_mun
LEFT JOIN gold.geo_municipio g  ON f.cve_mun  = g.cve_mun
LEFT JOIN gold.predicciones  p  ON f.cct      = p.cct
                               AND f.id_ciclo = p.id_ciclo
                               AND p.modelo   = 'ML-01'
WHERE e.latitud IS NOT NULL
  AND e.longitud IS NOT NULL
