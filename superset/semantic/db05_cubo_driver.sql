-- =============================================================================
-- db05_cubo_driver  ·  DB-05 Analisis por driver
-- -----------------------------------------------------------------------------
-- Historia   : US-211b  (Monserrat Xcaret Miranda Olivas, Celula 2)
--              REPUNTEO Y RE-ESCALA US-205 (Manuel Alejandro Serrania, C2)
-- Contrato   : 04_UX_Design/Cube_Specs_DB05_DB08.md  (DOC-CUBESPEC-DB0508) §3
-- Grano      : una fila por id_driver x cve_mun x nivel x id_ciclo
--
-- RE-ESCALA A RECOMENDACION (decision C2-US-205, ratifica Cube_Specs §8.3):
--   DB-05 pasa de analizar el driver OBSERVADO (d1..d6 del hecho, KPI-19
--   propuesto) a analizar el driver DOMINANTE de ML-02 (KPI-07 ratificado).
--   El cubo fisico gold.cubo_driver (C1) ya fue construido sobre
--   gold_ml_runtime.recomendaciones (no sobre el hecho): distingue el 0 real
--   (hay recomendaciones pero ninguna eligio ese driver: escuelas_driver = 0)
--   del SIN_DATO (el grupo no tiene recomendaciones: escuelas_driver NULL) y
--   publica los denominadores reales escuelas_con_recomendacion /
--   escuelas_sin_recomendacion en cada grupo.
--
-- REPUNTEO A CUBOS FISICOS (US-205 / US-113): passthrough 1:1 de
--   gold.cubo_driver. La lista de columnas es explicita; la capa semantica no
--   agrega (el cubo ya viene al grano DEC-009) ni filtra salidas de ML crudas.
--
-- FORMATO LARGO: una fila por driver. 'dimension_obligatoria_en_agregacion:
--   id_driver' en metrics_db05_db08.yaml documenta que ninguna metrica se suma
--   sin agrupar/filtrar por id_driver (si no se infla x6).
--
-- Reglas aplicadas: R2 (SIN_DATO nunca cero -- cobertura_recomendacion lo
--   gobierna), R5 (Gold ya viene acotado). R1/R3 viven en C1.
-- =============================================================================

SELECT
    -- ---------- identidad del driver ------------------------------------------
    cd.id_driver,                               -- filtro/selector: tab del driver
    cd.nombre_driver,
    cd.fuente_driver,
    cd.nivel_geografico        AS driver_nivel_geografico,

    -- ---------- identidad y llaves geograficas --------------------------------
    cd.cve_mun,
    cd.cve_ent,                                 -- filtro global: entidad
    cd.nombre_municipio,
    cd.nombre_entidad,
    cd.nivel,                                   -- filtro global: nivel educativo
    cd.id_ciclo,                                -- filtro global: ciclo
    cd.ciclo,
    cd.anio_inicio,

    -- ---------- componentes aditivos (del cubo C1, recomendacion) -------------
    cd.total_escuelas,
    cd.escuelas_con_recomendacion,
    cd.escuelas_sin_recomendacion,
    cd.escuelas_driver,                         -- NULL + SIN_DATO por grupo sin ML-02
    cd.cobertura_recomendacion                  -- OK / SIN_DATO

FROM gold.cubo_driver cd