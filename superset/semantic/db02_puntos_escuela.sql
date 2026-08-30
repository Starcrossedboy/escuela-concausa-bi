-- =============================================================================
-- db02_puntos_escuela  ·  DB-02 Mapa de riesgo territorial
-- -----------------------------------------------------------------------------
-- Historia : US-205  (Manuel Alejandro Serrania Reinada, Celula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §2 ("coropletico municipal + puntos de
--            escuela por indice de riesgo")
-- Grano    : una fila por cct x id_ciclo (grano del hecho, sin agregar)
--
-- REPUNTEO A CUBOS FISICOS (US-205 / US-113): la capa de puntos ya NO une a
--   gold.predicciones; consume gold.cubo_escuela_360 (grano cct x id_ciclo,
--   C1), que ya trae indice_riesgo / en_riesgo / cobertura_prediccion resueltos
--   por LEFT JOIN a la salida ML-01 (llave completa, modelo 'ML-01', umbral R3).
--   La capa semantica filtra solo escuelas georreferenciadas y anade el enrich
--   del nombre oficial INEGI del municipio.
--
-- Una escuela sin prediccion NO desaparece del mapa: viaja con
--   cobertura_prediccion = 'SIN_DATO' y en_riesgo nulo (desconocido, no falso),
--   invariante que garantiza el cubo C1 (R2).
--
-- Reglas aplicadas: R2 (SIN_DATO nunca cero), R5 (Gold ya viene acotado).
--   R1/R3 viven en el cubo C1.
-- =============================================================================

SELECT
    -- ---------- identidad ------------------------------------------------------
    s.cct,
    s.nombre_escuela                         AS nombre,
    s.nivel,                                     -- filtro global: nivel educativo
    s.sostenimiento,

    -- ---------- georreferencia -------------------------------------------------
    s.latitud,
    s.longitud,

    -- ---------- territorio y tiempo --------------------------------------------
    s.cve_mun,
    s.cve_ent,                                  -- filtro global: entidad
    COALESCE(g.nombre_municipio, s.nombre_municipio) AS nombre_municipio,
    s.nombre_entidad,
    s.id_ciclo,                                 -- filtro global: ciclo
    s.ciclo,
    s.anio_inicio,

    -- ---------- hechos observados ----------------------------------------------
    s.matricula_total,
    s.variacion_matricula,

    -- ---------- riesgo (ML-01, resuelto por el cubo C1) ------------------------
    s.indice_riesgo,
    s.en_riesgo,                               -- nulo sin prediccion, nunca FALSE
    s.cobertura_prediccion

FROM gold.cubo_escuela_360 s
LEFT JOIN gold.geo_municipio g ON s.cve_mun = g.cve_mun
WHERE s.latitud IS NOT NULL
  AND s.longitud IS NOT NULL