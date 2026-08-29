-- =============================================================================
-- db08_cubo_pivot  ·  DB-08 Explorador del cubo
-- -----------------------------------------------------------------------------
-- Historia   : US-211b  (Monserrat Xcaret Miranda Olivas, Celula 2)
--              REPUNTEO US-205 (Manuel Alejandro Serrania Reinada, C2)
-- Contrato   : 04_UX_Design/Cube_Specs_DB05_DB08.md  (DOC-CUBESPEC-DB0508) §4
-- Grano      : una fila por cct x id_driver x id_ciclo
--
-- REPUNTEO A CUBOS FISICOS (US-205 / US-113): passthrough de gold.cubo_pivot
--   (C1, grano de detalle). El formato largo (unpivot de d1..d6) y las coberturas
--   ya los resuelve el cubo; la capa semantica solo anade el enrich del catalogo
--   gold.dim_driver (fuente_driver / driver_nivel_geografico), dos columnas que
--   el cubo no expone.
--
-- v1 se conserva OBSERVADO (Cube_Specs §2.1): analiza el driver medido en el
--   hecho, no la prediccion. Fuera de alcance v1: banderas CEMABE crudas e
--   indice_riesgo/recomendacion (Cube_Specs §4.2). El cubo C1 expone de todos
--   modos cobertura_prediccion / cobertura_recomendacion para que el explorador
--   pueda cruzar con ML; aqui no se consumen (KPI-20 intacto).
--
-- Grano de detalle: AVG() es seguro en la capa semantica para 'valor_driver'
--   (no es promedio de promedios) y excluye NULL de forma nativa -- mismo
--   efecto que filtrar por cobertura_driver = 'OK' (Cube_Specs §4.3).
--
-- Reglas aplicadas: R2 (SIN_DATO nunca cero -- viaja cobertura_driver del cubo),
--   R5 (Gold ya viene acotado). R1/R3 no aplican a v1.
-- Sin GROUP BY: se esta al grano del detalle.
-- =============================================================================

SELECT
    -- ---------- identidad y llaves ---------------------------------------------
    cp.cct,
    cp.id_driver,
    cp.id_ciclo,                               -- filtro global: ciclo
    cp.ciclo,
    cp.anio_inicio,

    -- ---------- perfil de la escuela -------------------------------------------
    cp.nombre_escuela,
    cp.nivel,                                  -- filtro global: nivel educativo
    cp.sostenimiento,
    cp.cve_ent,                                -- filtro global: entidad
    cp.cve_mun,
    cp.nombre_municipio,
    cp.nombre_entidad,

    -- ---------- identidad del driver (catalogo enrich) ------------------------
    cp.nombre_driver,
    dd.fuente            AS fuente_driver,
    dd.nivel_geografico  AS driver_nivel_geografico,

    -- ---------- valor y cobertura -----------------------------------------------
    cp.valor_driver,
    cp.cobertura_driver,

    -- ---------- contexto (repetido x6, formato largo) ---------------------------
    cp.matricula_total,
    cp.indice_completitud_drivers

FROM gold.cubo_pivot cp
LEFT JOIN gold.dim_driver dd ON cp.id_driver = dd.id_driver