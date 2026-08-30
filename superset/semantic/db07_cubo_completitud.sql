-- =============================================================================
-- Completitud de drivers (KPI-05, KPI-06)  ·  DB-07 Calidad y cobertura de datos
-- -----------------------------------------------------------------------------
-- Historia : US-222 (Oscar Antonio Quiroz Lázaro, Célula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §4 (KPI-05, KPI-06)
-- Grano    : cve_mun × nivel × id_driver × id_ciclo (igual que gold.cubo_completitud)
--
-- Es casi un SELECT * sobre el cubo ya materializado por C1 (US-113):
-- gold.cubo_completitud ya trae los componentes aditivos listos.
-- Las razones se calculan downstream (Superset), nunca aquí:
--   completitud_promedio = SUM(suma_completitud) / NULLIF(SUM(total_escuelas), 0)
--   pct_sin_dato         = SUM(escuelas_sin_dato) / NULLIF(SUM(total_escuelas), 0)
-- =============================================================================
SELECT
    cve_mun,
    cve_ent,
    nombre_municipio,
    nombre_entidad,
    nivel,
    id_ciclo,
    ciclo,
    anio_inicio,
    id_driver,
    nombre_driver,
    total_escuelas,
    escuelas_con_dato,
    escuelas_sin_dato,
    suma_completitud,
    cobertura_driver
FROM gold.cubo_completitud