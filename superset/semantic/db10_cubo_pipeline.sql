-- =============================================================================
-- Estado de la ingesta (KPI-13)  ·  DB-10 Monitor del pipeline
-- -----------------------------------------------------------------------------
-- Historia : US-223 (Oscar Antonio Quiroz Lázaro, Célula 2 - Analytics & BI)
-- Contrato : 04_UX_Design/Screen_Specs.md §4 (KPI-13)
-- Grano    : id_fuente × fecha_ingesta (igual que gold.cubo_pipeline)
--
-- Casi un SELECT * sobre el cubo materializado por C1 (US-113). `filas` es
-- un componente aditivo: la razón/total se calcula downstream (Superset)
-- como SUM(filas), nunca aquí. Una fuente sin ingesta conserva su fila de
-- catálogo con cobertura_pipeline='SIN_DATO', nunca desaparece ni cuenta 0.
-- =============================================================================
SELECT
    id_fuente,
    fuente,
    fecha_ingesta,
    filas,
    _ingested_at,
    source_url,
    cobertura_pipeline,
    CASE WHEN cobertura_pipeline = 'OK' THEN 1 ELSE 0 END AS es_ok,
    CASE WHEN cobertura_pipeline = 'SIN_DATO' THEN 1 ELSE 0 END AS es_sin_dato
FROM gold.cubo_pipeline